# Cloud Agent — Hands-On Exercises

A working multi-agent system with **20 implementations removed**. Each `TODO`
is 1–10 lines. The scaffolding, prompts, imports and tests are all intact — you
write only the logic that teaches something.

Every TODO block states: **GOAL** (what to build), **WHY** (the concept),
**STEPS**, **HINT** (the trap), **CHECK** (how to prove it works), **SIZE**.

```
Progress:  python check_progress.py
```

## Setup

Follow `instruction.md` Parts 0–5 first — conda env, `agent/.env`, and the four
backing services (MySQL, Redis, Milvus, Neo4j). Nothing here runs until those
are up.

Add your own key to `agent/.env`:

```
OPENAI_API_KEY=sk-REPLACE-WITH-YOUR-OWN-KEY
```

## Do them in this order

Dependencies are real — TODO 04 cannot work before TODO 02.

### Stage 1 · State & graph wiring (`core/workflow/`)
Start here: until the graph is assembled, nothing else can be exercised.

| # | File | Builds |
|---|---|---|
| 01 | `state.py` | The 5 state keys every node reads/writes |
| 02 | `graph_manager.py` | The billing → FinOps branch condition |
| 03 | `graph_manager.py` | Orchestrator → 4 sub-agents routing edges |
| 04 | `graph_manager.py` | The conditional edge that enables the handoff |

**Checkpoint:** `python core/workflow/graph_manager.py` runs a 2-turn smoke test.

### Stage 2 · Routing (`agents/orchestrator.py`)
| # | Builds |
|---|---|
| 05 | The classification LLM call |
| 06 | Text label → node name, including the FinOps flag |

**Checkpoint:** "what is a VPC" → product; "my orders" → billing; "cut my costs" → finops.

### Stage 3 · Agents & tool security (`agents/`)
TODO 07 is the one to slow down on — it is the security lesson of the project.

| # | File | Builds |
|---|---|---|
| 07 | `billing_agent.py` | **Interceptor forcing the real `user_id` into every tool call** |
| 08 | `billing_agent.py` | MCP client + 2-tool allowlist |
| 09 | `finops_agent.py` | The FinOps analysis toolset |
| 10 | `product_agent.py` | The inner ReAct agent + message return contract |
| 11 | `recommendation_agent.py` | Hybrid local-`@tool` + MCP toolset |
| 12 | `promotion_agent.py` | The 4-tool marketing set |

**Checkpoint:** `python agents/billing_agent.py` runs a built-in prompt-injection
attack. Ask it for `user_1002`'s orders while logged in as `user_1001` — it must
refuse. If it succeeds, TODO 07 is wrong.

### Stage 4 · MCP (`core/mcp/`)
| # | Builds |
|---|---|
| 13 | Config loading that fails loudly |
| 14 | Connect + runtime tool discovery (idempotent) |

### Stage 5 · Memory (`core/memory/`)
| # | File | Builds |
|---|---|---|
| 15 | `short_term.py` | The per-user Redis key — the isolation boundary |
| 16 | `short_term.py` | Save with TTL + compression trigger |
| 17 | `short_term.py` | Trim policy that preserves system messages |
| 18 | `long_term.py` | Embed + insert into Milvus |
| 19 | `long_term.py` | Filtered vector search |

**Checkpoint:** `redis-cli TTL <key>` counts down (not `-1`). Save a preference as
user A, query as user B — B must get nothing back.

### Stage 6 · RAG tool (`tools/`)
| # | Builds |
|---|---|
| 20 | `vector_tool.py` | Retrieve doc chunks and format them so the agent can cite sources |

**Final:** `python agent/main.py`, then the full app per `instruction.md` Part 6+.

## The four ideas this project teaches

1. **A graph, not a chain.** Nodes are agents; edges are runtime decisions. TODOs 02–04.
2. **Never trust the model with identity.** The LLM proposes tool arguments; the
   interceptor overwrites `user_id` before execution. TODO 07.
3. **Least privilege per agent.** Same MCP server, different allowlists. TODOs 08/09/12.
4. **Two-tier memory.** Redis forgets on a TTL; Milvus remembers by similarity. TODOs 15–19.

## Working method

- Do one TODO, run its **CHECK**, then delete the banner comment.
- `raise NotImplementedError` marks the spot. Six TODOs have no stub — the code
  below them will `NameError` until you define the variable. That is expected.
- Stuck? The docstring above each function is the spec, and `reference.md`
  documents the architecture.
