import os
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_neo4j import Neo4jGraph
from langchain_neo4j import GraphCypherQAChain
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

# Global singletons to avoid reconnecting on every tool call
_graph_chain_instance = None
_graph_instance = None

def _get_graph_chain():
    """Get the GraphCypherQAChain singleton."""
    global _graph_chain_instance, _graph_instance
    if _graph_chain_instance is not None:
        return _graph_chain_instance

    print("🔌 [Init] Connecting to Neo4j database...")
    graph = Neo4jGraph(
        url=os.getenv("NEO4J_URI", "bolt://YOUR_NEO4J_HOST:7687"),
        username=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "YOUR_NEO4J_PASSWORD")
    )
    _graph_instance = graph
    graph.refresh_schema()

    llm = ChatOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("MODEL", "gpt-4o"),
        base_url=os.getenv("BASE_URL") or None,
        temperature=0,
    )

    CYPHER_GENERATION_TEMPLATE = """Task:Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.

Schema:
{schema}

Important Rules:
1. Node labels: Region, Zone, InstanceTypeFamily, InstanceType, Storage, BillingRule, etc.
2. Property access: if you use a RETURN clause to return a property, you must assign a variable to the node in the preceding MATCH clause!
   Wrong: MATCH (:InstanceType {{id: "g8a"}}) RETURN vcpu
   Correct: MATCH (i:InstanceType {{id: "ecs.g8a.4xlarge"}}) RETURN i.vcpu
3. Entity hierarchy: g8a, c7, etc. belong to InstanceTypeFamily. Specific model names like ecs.g8a.xlarge belong to InstanceType.
4. Return format: return as much detail as possible; when returning nodes use RETURN node, not just the ID.

The question is:
{question}"""

    cypher_prompt = PromptTemplate(
        template=CYPHER_GENERATION_TEMPLATE,
        input_variables=["schema", "question"]
    )

    _graph_chain_instance = GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph,
        cypher_prompt=cypher_prompt,
        verbose=False, # Disable verbose logging during tool calls to keep output clean
        return_intermediate_steps=False, 
        allow_dangerous_requests=True,
    )
    return _graph_chain_instance

def _extract_keywords(query: str) -> list[str]:
    lower_query = query.lower()
    tokens = re.findall(r"[a-z0-9._-]+", lower_query)
    cn_tokens = re.findall(r"[\u4e00-\u9fff]{2,}", query)
    keywords = []
    for token in tokens + cn_tokens:
        if len(token.strip()) >= 2 and token not in keywords:
            keywords.append(token.strip())
    if not keywords:
        keywords.append(lower_query[:20] if lower_query else "ecs")
    return keywords[:8]

def _fallback_graph_keyword_search(query: str) -> str:
    global _graph_instance
    if _graph_instance is None:
        _get_graph_chain()
    
    graph = _graph_instance
    if graph is None:
        return "Graph keyword search unavailable, please try again later."

    keywords = _extract_keywords(query)
    
    # Neo4j cannot dynamically unpack a $keywords list for CONTAINS matching in ANY/WHERE,
    # so we build the OR clauses in Python instead.
    
    where_clauses = []
    for k in keywords:
        where_clauses.append(f"toLower(coalesce(n.id, '')) CONTAINS '{k}' OR toLower(coalesce(n.name, '')) CONTAINS '{k}' OR toLower(coalesce(n.description, '')) CONTAINS '{k}'")
    node_where = " OR ".join(where_clauses)
    
    node_cypher = f"""
    MATCH (n)
    WHERE {node_where}
    RETURN labels(n) AS labels, coalesce(n.id, n.name, '') AS node_key, properties(n) AS props
    LIMIT 8
    """
    
    rel_where_clauses = []
    for k in keywords:
        rel_where_clauses.append(f"toLower(coalesce(a.id, '')) CONTAINS '{k}' OR toLower(coalesce(a.name, '')) CONTAINS '{k}' OR toLower(coalesce(b.id, '')) CONTAINS '{k}' OR toLower(coalesce(b.name, '')) CONTAINS '{k}'")
    rel_where = " OR ".join(rel_where_clauses)

    rel_cypher = f"""
    MATCH (a)-[r]->(b)
    WHERE {rel_where}
    RETURN labels(a) AS from_labels, coalesce(a.id, a.name, '') AS from_node,
           type(r) AS rel, labels(b) AS to_labels, coalesce(b.id, b.name, '') AS to_node
    LIMIT 8
    """

    try:
        nodes = graph.query(node_cypher)
        relations = graph.query(rel_cypher)
    except Exception as exc:
        return f"Graph keyword search failed: {str(exc)}"

    if not nodes and not relations:
        return "No relevant graph information found."

    parts = ["Graph keyword search results:"]
    if nodes:
        parts.append("Matched nodes:")
        for row in nodes:
            labels = ",".join(row.get("labels", []))
            node_key = row.get("node_key", "")
            props = row.get("props", {})
            parts.append(f"- [{labels}] {node_key} {props}")
    if relations:
        parts.append("Matched relationships:")
        for row in relations:
            from_labels = ",".join(row.get("from_labels", []))
            to_labels = ",".join(row.get("to_labels", []))
            parts.append(f"- [{from_labels}] {row.get('from_node', '')} -[{row.get('rel', '')}]-> [{to_labels}] {row.get('to_node', '')}")
    return "\n".join(parts)

@tool
def query_knowledge_graph(query: str) -> str:
    """
    Query the cloud product knowledge graph.
    Use this tool when the user asks about cloud product architecture, containment relationships, or configuration constraints
    (e.g., how many NICs can ecs.g8a.xlarge attach? Which instances are available in Beijing zones? What are the refund restrictions?).
    The input parameter query must be a clear natural-language question.
    """
    try:
        chain = _get_graph_chain()
        result = chain.invoke({"query": query})
        return result.get('result', "No relevant graph information found.")
    except Exception as e:
        fallback_result = _fallback_graph_keyword_search(query)
        if fallback_result and "failed" not in fallback_result:
            return fallback_result
        return f"Error querying knowledge graph: {str(e)}; keyword fallback result: {fallback_result}"
