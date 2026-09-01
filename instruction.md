# Cloud Agent — End-to-End Setup & Demo Runbook

This document is the single source of truth for getting the multi-agent cloud customer-service app from a clean state to a fully working demo.

The project consists of:

- **Backend** — FastAPI app under `app/` that exposes `POST /api/chat` (SSE streaming) and orchestrates a LangGraph multi-agent workflow defined under `agent/`.
- **Frontend** — Vue 3 + Vite app under `front/cloud_agent/`.
- **Backing services**:
  - **MySQL** (required) — orders, instances, daily metrics. Used by BillingAgent + FinOpsAgent.
  - **Milvus** (recommended) — semantic cache + long-term memory.
  - **Redis** (recommended) — short-term conversation memory.
  - **Neo4j** (optional) — knowledge graph for the ProductAgent.
- **LLM** — OpenAI `gpt-4o` for chat, `text-embedding-3-small` for embeddings.

---

## Part 0 — Prerequisites (one-time)

Verify these are installed:

```bash
conda --version           # Anaconda / Miniconda
docker --version          # Docker Desktop running
node --version && npm -v  # Node 18+
```

Activate the project's conda environment:

```bash
conda activate multi_agent
```

Install Python and frontend dependencies:

```bash
cd /Users/andyli/projects/real_projects/cloud_agent
pip install -r agent/requirements.txt

cd front/cloud_agent
npm install
```

---

## Part 1 — Clean teardown (start from a known-empty state)

Run these commands in any terminal. They are idempotent; each step will silently succeed if the resource is already gone.

### 1.1 Kill running app processes

```bash
# Backend (uvicorn on 8090)
lsof -ti tcp:8090 | xargs kill -9 2>/dev/null

# Frontend (Vite — usually 5174, sometimes 5173)
lsof -ti tcp:5173 | xargs kill -9 2>/dev/null
lsof -ti tcp:5174 | xargs kill -9 2>/dev/null

# Frontend (Vite — usually 5174, sometimes 5173)
lsof -ti tcp:5173 | xargs kill -9 2>/dev/null
lsof -ti tcp:5174 | xargs kill -9 2>/dev/null
```

### 1.2 Wipe MySQL data (drop + recreate the container)

```bash
docker rm -f cloud-agent-mysql 2>/dev/null

docker run -d --name cloud-agent-mysql \
  -e MYSQL_ROOT_PASSWORD=cloudpass \
  -e MYSQL_DATABASE=cloud_platform \
  -p 3306:3306 \
  --restart unless-stopped \
  mysql:8 \
  --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci

# Wait for MySQL to finish initializing
until docker exec cloud-agent-mysql mysqladmin ping -uroot -pcloudpass --silent 2>/dev/null; do
  echo "waiting for MySQL..."; sleep 2
done
echo "MySQL ready."
```

### 1.3 Wipe Milvus collections used by this app

```bash
# Drop the two collections this app owns; leaves other Milvus tenants alone.
python - <<'PY'
from pymilvus import MilvusClient
c = MilvusClient(uri="http://127.0.0.1:19530")
for col in ("qa_semantic_cache", "long_term_memory"):
    if c.has_collection(col):
        c.drop_collection(col)
        print(f"dropped {col}")
    else:
        print(f"{col} not present")
PY
```

> If Milvus is not running, this script raises a connection error — that's fine, there's nothing to drop.

### 1.4 Wipe short-term memory keys in Redis

```bash
# Only deletes keys this app uses; other Redis tenants are unaffected.
docker exec redis redis-cli -a Yoxxxxxx --no-auth-warning \
  --scan --pattern 'memory:short:*' \
  | xargs -r -n 100 docker exec -i redis redis-cli -a Yoxxxxxx --no-auth-warning DEL
```

### 1.5 Wipe the Neo4j knowledge graph (optional)

Only needed if you previously ran `build_kg.py` and want a fresh ingestion:

```bash
docker exec neo4j cypher-shell -u neo4j -p 12345678 \
  "MATCH (n) DETACH DELETE n;"
```

### 1.6 Sanity check — what's running

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" \
  | grep -E "(mysql|redis|milvus-standalone|neo4j|cloud-agent)"
lsof -ti tcp:8090,5173,5174 2>/dev/null && echo "still running" || echo "no app processes on 8090/5173/5174"
```

You should see all four containers `Up`, and no app processes on the listed ports.

---

## Part 2 — Configure `agent/.env`

Open `agent/.env` and verify these values. Replace `OPENAI_API_KEY` with your real key.

```bash
# REQUIRED
OPENAI_API_KEY=sk-proj-...your-real-key...
MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small

# REQUIRED for BillingAgent / FinOpsAgent
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=cloudpass
MYSQL_DATABASE=cloud_platform

# Recommended (memory + cache)
REDIS_URL=redis://default:Yoxxxxxx@127.0.0.1:6379
REDIS_TTL=1800
MILVUS_HOST=127.0.0.1
MILVUS_PORT=19530
MILVUS_API_KEY=

# Optional (knowledge graph)
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=12345678
NEO4J_DATABASE=neo4j

LOG_LEVEL=INFO
```

Verify the OpenAI key works (independent of the app):

```bash
KEY=$(grep '^OPENAI_API_KEY' agent/.env | cut -d= -f2)
curl -sS -o /dev/null -w "OpenAI: %{http_code}\n" \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o","messages":[{"role":"user","content":"ping"}]}' \
  https://api.openai.com/v1/chat/completions
# Expect: OpenAI: 200
```

---

## Part 3 — Confirm the four backing services are healthy

```bash
echo "--- MySQL ---"
docker exec cloud-agent-mysql mysql -uroot -pcloudpass cloud_platform \
  -e "SELECT 'OK' AS status;" 2>&1 | grep -v "Using a password"

echo "--- Redis ---"
docker exec redis redis-cli -a Yoxxxxxx --no-auth-warning PING

echo "--- Milvus ---"
code=$(curl -sS -m 5 -o /dev/null -w "%{http_code}" http://127.0.0.1:9091/healthz 2>/dev/null)
if [ "$code" = "200" ]; then
  echo "Milvus: OK (HTTP 200)"
else
  echo "Milvus: DOWN (curl code ${code:-000}) - semantic cache + long-term memory disabled"
fi

echo "--- Neo4j ---"
if docker exec neo4j cypher-shell -u neo4j -p 12345678 \
     "RETURN 'OK' AS status;" 2>/dev/null | grep -q '"OK"'; then
  echo "Neo4j: OK"
else
  echo "Neo4j: DOWN - ProductAgent knowledge graph unavailable"
fi
```

Each line should report `OK` (or `PONG` for Redis).

If a container exists but is stopped, start it:

```bash
docker start cloud-agent-mysql redis milvus-standalone neo4j 2>&1
```

If `docker start` says `**No such container**`, it was never created on this
machine - create it once, then it can be started/stopped from then on:

```bash
# Milvus standalone (embedded etcd + MinIO; creates container "milvus-standalone").
# Pull from the 2.6 branch, NOT master: master installs server v3.0.0, which is a
# major-version mismatch with the pinned pymilvus 2.6.x client. The 2.6 script
# installs server v2.6.x. Run it from the project root; it writes ./volumes/milvus
# (already in .gitignore) and binds ports 19530, 9091 and 2379.
curl -sSf https://raw.githubusercontent.com/milvus-io/milvus/2.6/scripts/standalone_embed.sh \
  -o standalone_embed.sh

# The upstream script prefixes every docker call with `sudo`, which is unnecessary
# with Docker Desktop and makes the script prompt for your macOS login password
# ("Password:" then "Sorry, try again." if it is wrong or empty - sudo echoes
# NOTHING as you type). Strip it before running:
sed -i '' 's/sudo //g' standalone_embed.sh      # macOS/BSD sed; use `sed -i` on Linux

bash standalone_embed.sh start

# Neo4j (password must match NEO4J_PASSWORD in agent/.env; min 8 chars).
# Data/logs are bind-mounted so the graph survives a container rebuild.
#docker run -d --name neo4j \
#  -p 7474:7474 -p 7687:7687 \
#  -e NEO4J_AUTH=neo4j/12345678 \
#  -v "$(pwd)/volumes/neo4j/data:/data" \
#  -v "$(pwd)/volumes/neo4j/logs:/logs" \
#  neo4j:5

# Bolt takes ~5-30s after the container reports Up; wait before running Part 5:
until docker exec neo4j cypher-shell -u neo4j -p 12345678 "RETURN 1;" >/dev/null 2>&1; do
  sleep 3
done; echo "Neo4j bolt ready"
```

Both are degrade-gracefully services: with Milvus down the semantic cache and
long-term memory are disabled, and with Neo4j down the ProductAgent falls back
to answering without the knowledge graph. The basic chat path still works.

---

## Part 4 — Load MySQL seed data

The seed script creates `cloud_orders`, `cloud_instances`, `instance_metrics_daily` and inserts mock data for `user_1001` (which the frontend hardcodes) and `user_1002`.

```bash
cd /Users/andyli/projects/real_projects/cloud_agent

docker exec -i cloud-agent-mysql mysql -uroot -pcloudpass cloud_platform \
  < agent/database/init_mock_data.sql 2>&1 | grep -v "Using a password"

# Verify
docker exec cloud-agent-mysql mysql -uroot -pcloudpass cloud_platform -e "
SELECT user_id, COUNT(*) AS orders FROM cloud_orders GROUP BY user_id;
SELECT user_id, COUNT(*) AS instances FROM cloud_instances GROUP BY user_id;
SELECT instance_id, COUNT(*) AS metric_rows FROM instance_metrics_daily GROUP BY instance_id;
" 2>&1 | grep -v "Using a password"
```

Expected:


| Check                    | Expected                                           |
| ------------------------ | -------------------------------------------------- |
| `cloud_orders`           | `user_1001 = 3`, `user_1002 = 3`                   |
| `cloud_instances`        | `user_1001 = 2`, `user_1002 = 1`                   |
| `instance_metrics_daily` | `i-bp1_user1001_ecs = 7`, `i-bp1_user1002_ecs = 7` |


---

## Part 5 — Build the Neo4j knowledge graph (optional)

Only required for ProductAgent graph queries (e.g. "How many ENIs can ecs.g8a.4xlarge attach?"). Skip if you don't plan to demo the graph tool.

`build_kg.py` reads a markdown file, uses gpt-4o to extract entities and relationships, and `MERGE`s them into Neo4j. Each file takes ~30–60 s and a small amount of OpenAI credits.

```bash
conda activate multi_agent
cd /Users/andyli/projects/real_projects/cloud_agent

# Most graph-rich source
python agent/test/build_kg.py mock_data/ecs_product_info.md

# Optional — for richer coverage
python agent/test/build_kg.py mock_data/ecs_network_security.md
python agent/test/build_kg.py mock_data/billing_and_refund_policy.md
python agent/test/build_kg.py mock_data/rds_product_info.md
```

Verify nodes were ingested:

```bash
docker exec neo4j cypher-shell -u neo4j -p 12345678 \
  "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count ORDER BY count DESC;"
```

You should see labels like `InstanceType`, `Region`, `Storage`, `BillingRule`, `Feature` with non-zero counts.

---

## Part 6 — Warm the L1 semantic cache (optional)

Pre-loads four high-frequency English Q&A pairs (refund rules, VPC pricing, etc.) into Milvus so they return instantly without going through the agent graph. Only useful if Milvus is up.

```bash
conda activate multi_agent
cd /Users/andyli/projects/real_projects/cloud_agent/app
python preload_cache.py
```

Expected output:

```
Warming up the L1 semantic cache...
Injecting -> Query: 'What are the refund rules for ECS cloud servers?'
Injecting -> Query: 'How long does a refund take to arrive?'
Injecting -> Query: 'How long is your Cloud Architect course valid?'
Injecting -> Query: 'How is VPC billed?'
Cache warmup complete.
```

---

## Part 7 — Start the backend (Terminal A)

```bash
conda activate multi_agent
cd /Users/andyli/projects/real_projects/cloud_agent/app
uvicorn app_main:app --host 0.0.0.0 --port 8090 --reload
```

Healthy startup looks like:

```
INFO:     Uvicorn running on http://0.0.0.0:8090
Initializing multi-agent graph...
Initializing memory subsystem...
Agent system ready.
INFO:     Application startup complete.
```

Smoke-test from another shell:

```bash
curl -sS http://127.0.0.1:8090/docs -o /dev/null -w "docs: %{http_code}\n"
# Expect: docs: 200
```

---

## Part 8 — Start the frontend (Terminal B)

```bash
cd /Users/andyli/projects/real_projects/cloud_agent/front/cloud_agent
npm run dev
```

Vite prints a URL like `http://localhost:5174/`. Open it in a browser.

---

## Part 9 — Demo queries

The frontend hardcodes `user_id = "user_1001"` (the user populated by the seed). Click a scenario card or type your own. Each row below is verified by Part 1–6 setup.

### Routing to ProductAgent (RAG + Knowledge Graph)


| Query                                                                                                                       | Hits                    |
| --------------------------------------------------------------------------------------------------------------------------- | ----------------------- |
| "What are the basic properties of ECS cloud servers?"                                                                       | Vector RAG (Milvus)     |
| "How many ENIs and storage volumes can the ecs.g8a.4xlarge instance attach, and which availability zones is it offered in?" | Neo4j (requires Part 5) |
| "What's the difference between c7 (compute-optimized) and g8a (general-purpose) families?"                                  | Neo4j                   |


### Routing to BillingAgent (MySQL)


| Query                              | Hits              |
| ---------------------------------- | ----------------- |
| "Show me my recent orders"         | `cloud_orders`    |
| "List all of my running instances" | `cloud_instances` |


### Routing to FinOpsAgent (MySQL metrics + analysis)


| Query                                                      | Hits                     |
| ---------------------------------------------------------- | ------------------------ |
| "Pull the last 7 days of metrics and suggest cost savings" | `instance_metrics_daily` |
| "My server utilization is low. How can I save money?"      | metrics + recommendation |


### Routing to PromotionAgent (in-memory campaign data + image gen)


| Query                                             | Hits                                          |
| ------------------------------------------------- | --------------------------------------------- |
| "I want to promote ECS — do you have a poster?"   | `get_promotion_materials`                     |
| "Generate a promotional poster for the c7 family" | qwen-image-2.0 (requires `DASHSCOPE_API_KEY`) |


### What you should see in Terminal A per request

```
INFO:  127.0.0.1:xxxxx - "POST /api/chat HTTP/1.1" 200 OK
Entering agent workflow...
[BillingAgent] Handling order/billing query...
```

with no traceback at the end.

---

## Part 10 — Shut everything down

```bash
# App processes
lsof -ti tcp:8090 | xargs kill -9 2>/dev/null
lsof -ti tcp:5173 | xargs kill -9 2>/dev/null
lsof -ti tcp:5174 | xargs kill -9 2>/dev/null

# Containers (stop only — data persists in volumes)
docker stop cloud-agent-mysql redis milvus-standalone neo4j 2>/dev/null
```

To completely destroy the MySQL data and start fresh, jump back to Part 1.2.

---

## Troubleshooting


| Symptom                                                    | Cause                                                      | Fix                                                                                                                    |
| ---------------------------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `Address already in use` on uvicorn                        | Another process holds 8090                                 | **Identify it first:** `lsof -nP -iTCP:8090 -sTCP:LISTEN`**.** If it is a stale `uvicorn`/`python`, `lsof -ti tcp:8090 |
| `openai.AuthenticationError 401`                           | Bad `OPENAI_API_KEY`                                       | Re-run the curl probe in Part 2                                                                                        |
| `Can't connect to MySQL server on '127.0.0.1'`             | MySQL down                                                 | `docker start cloud-agent-mysql`                                                                                       |
| `Table 'cloud_platform.cloud_orders' doesn't exist`        | Seed not loaded                                            | Re-run Part 4                                                                                                          |
| `NOAUTH` / `WRONGPASS` from Redis                          | `REDIS_URL` uses a username the server has no ACL user for | Use `redis://default:Yoxxxxxx@127.0.0.1:6379` - with plain `requirepass` the only user is `default`, not `root`        |
| `Neo4j connection unauthorized`                            | Wrong password                                             | Confirm `NEO4J_PASSWORD=12345678` in `.env`                                                                            |
| `SemanticCache init failed` warning                        | Milvus down (non-fatal)                                    | `docker start milvus-standalone` if you want cache                                                                     |
| BillingAgent crashes with `ModuleNotFoundError: 'pymysql'` | Deps drift                                                 | `pip install -r agent/requirements.txt`                                                                                |
| Frontend "Request failed (FastAPI port 8090)"              | uvicorn crashed mid-stream                                 | Check Terminal A traceback                                                                                             |
| `FileNotFoundError: 'agent'` from MCP subprocess           | Stale uvicorn before mcp_loader fix                        | Restart uvicorn                                                                                                        |
| ProductAgent says "no graph info found"                    | Neo4j is empty                                             | Run Part 5                                                                                                             |


---

## Quick reference — what lives where

```
cloud_agent/
├── agent/
│   ├── .env                      # OPENAI_API_KEY + DB credentials
│   ├── agents/                   # 6 agent nodes (orchestrator, billing, finops, ...)
│   ├── core/                     # workflow graph, memory, MCP, KG modules
│   ├── config/
│   │   ├── settings.py           # pydantic-settings
│   │   ├── mcp_servers.json      # MCP child-process config
│   │   └── mcp_loader.py         # resolves relative cwd in mcp_servers.json
│   ├── database/
│   │   └── init_mock_data.sql    # MySQL seed (Part 4)
│   ├── mcp_servers/
│   │   └── cloud_platform_server.py   # FastMCP tools (DB queries, poster gen)
│   ├── test/
│   │   ├── build_kg.py           # Neo4j ingestion (Part 5)
│   │   ├── graphrag_chat.py      # standalone graph chat
│   │   └── milvus_rag.py         # standalone vector RAG
│   └── tools/                    # query_vector_db, query_knowledge_graph
├── app/
│   ├── app_main.py               # FastAPI entry point
│   ├── service/chat_service.py   # SSE streaming + agent invocation
│   ├── infra/cache.py            # Milvus L1 semantic cache
│   ├── preload_cache.py          # Cache warmup script (Part 6)
│   └── router/chat.py            # POST /api/chat
├── front/cloud_agent/            # Vue 3 + Vite frontend
└── mock_data/                    # Markdown + JSON knowledge base (RAG / KG sources)
```

