import os
import json
from typing import List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load .env environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

# ==========================================
# 1. Define general-purpose Pydantic data models
# ==========================================
class Property(BaseModel):
    key: str = Field(description="Property key name, e.g. vCPU, memory, storage_type, bandwidth_limit, error_code")
    value: str = Field(description="Property value, e.g. 4, 16GiB, ESSD, 10Gbps, 404")

class Node(BaseModel):
    id: str = Field(description="Unique node identifier, should be concise and unambiguous. E.g. ecs.g8a.xlarge, China North 2 (Beijing), Subscription")
    label: str = Field(description="Node type label. E.g. Product, Region, InstanceType, Storage, Image, BillingRule, ErrorCode, Feature")
    properties: List[Property] = Field(description="List of node properties", default_factory=list)

class Edge(BaseModel):
    source: str = Field(description="Source node ID")
    target: str = Field(description="Target node ID")
    type: str = Field(description="Relationship type in UPPER_SNAKE_CASE, e.g. CONTAINS, SUPPORTS, HAS_LIMIT, REQUIRES, RESOLVED_BY, BELONGS_TO")

class KnowledgeGraph(BaseModel):
    nodes: List[Node] = Field(description="List of all core entity nodes extracted from the document")
    edges: List[Edge] = Field(description="List of relationship mappings between entities extracted from the document")

# ==========================================
# 2. LLM extraction logic (compatible with Qwen and dynamic documents)
# ==========================================
def extract_knowledge_graph(file_path: str) -> dict:
    print(f"📄 Reading document: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Read configuration from environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    model_name = os.getenv("MODEL", "gpt-4o")
    base_url = os.getenv("BASE_URL") or None

    if not api_key:
        raise ValueError("❌ OPENAI_API_KEY not found in environment variables")

    # Initialize the LLM (OpenAI gpt-4o)
    llm = ChatOpenAI(
        api_key=api_key,
        model=model_name,
        base_url=base_url,
        temperature=0, # Ensure deterministic extraction
    )
    
    # Bind structured output
    structured_llm = llm.with_structured_output(KnowledgeGraph)

    # General-purpose prompt with chunking context hint
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a senior cloud-service knowledge graph architect. Your task is to read a fragment of cloud platform product documentation and extract the core knowledge graph from it.

        Extraction principles:
        1. **Nodes**: Identify core entities in the document.
           - Entities can be products (Product), regions (Region), instance types (InstanceType), storage types (Storage), billing modes (BillingRule), features (Feature), error codes (ErrorCode), etc.
           - Node IDs must be unique; prefer standard full names (e.g., "China North 2 (Beijing)" rather than "Beijing") so that nodes extracted from different document fragments can be merged.
           - Extract key numeric values or descriptions as node properties (Properties).
        2. **Edges**: Identify constraints and associations between entities.
           - Relationship types should be concise and uppercase (e.g., SUPPORTS, CONTAINS, RESTRICTS, REQUIRES, HAS_FEATURE).
        3. **Generality**: Flexibly define reasonable node labels and relationship types based on context.

        Note: You may be reading a single chunk of a longer document. Extract as many complete, self-contained entities and relationships as possible; do not omit important information from the current fragment.
        Ensure the output strictly conforms to the JSON Schema. All source and target values must reference node IDs present in the extracted nodes."""),
        ("human", "Document fragment content is as follows; please extract the knowledge graph:\n{text}")
    ])

    chain = prompt | structured_llm
    
    # ==========================================
    # Long-document chunking logic
    # ==========================================
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,       # Max characters per chunk (adjust based on model context window)
        chunk_overlap=200,     # Overlap between chunks to preserve context continuity
        separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""]
    )
    
    chunks = text_splitter.split_text(content)
    print(f"🔪 Document split into {len(chunks)} chunks, starting extraction...")

    all_nodes = {}  # Dict for deduplication, keyed by node_id
    all_edges = set() # Set for deduplication, stores tuple(source, type, target)
    
    for i, chunk in enumerate(chunks):
        print(f"⏳ Processing chunk {i+1}/{len(chunks)}...")
        try:
            kg_result = chain.invoke({"text": chunk})
            
            # Merge nodes (deduplicate and merge properties)
            for node in kg_result.nodes:
                node_id = node.id
                if node_id not in all_nodes:
                    all_nodes[node_id] = node
                else:
                    # If node already exists, try to merge new properties
                    existing_props = {p.key: p.value for p in all_nodes[node_id].properties}
                    for new_prop in node.properties:
                        if new_prop.key not in existing_props:
                            all_nodes[node_id].properties.append(new_prop)
                            
            # Merge edges (deduplicate)
            for edge in kg_result.edges:
                edge_tuple = (edge.source, edge.type, edge.target)
                all_edges.add(edge_tuple)
                
        except Exception as e:
            print(f"⚠️ Chunk {i+1} extraction failed, skipping: {e}")
            continue

    # Reassemble the final KnowledgeGraph
    final_kg = {
        "nodes": [node.dict() for node in all_nodes.values()],
        "edges": [{"source": e[0], "type": e[1], "target": e[2]} for e in all_edges]
    }
    
    output_json = file_path.replace('.md', '.json')
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(final_kg, f, ensure_ascii=False, indent=2)
    
    print(f"✅ All chunks extracted and merged! Total: {len(final_kg['nodes'])} nodes, {len(final_kg['edges'])} relationships. JSON saved to: {output_json}")
    return final_kg

# ==========================================
# 3. Neo4j import logic
# ==========================================
def import_to_neo4j(kg_data: dict):
    # Read Neo4j configuration from .env
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    
    print(f"🔌 Connecting to Neo4j database ({uri})...")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    with driver.session() as session:
        # Graph clearing removed; use incremental import (MERGE semantics) instead
        # print("🧹 Clearing existing graph data (for testing)...")
        # session.run("MATCH (n) DETACH DELETE n")

        print("🛠️ Importing nodes...")
        for node in kg_data['nodes']:
            label = node['label'].replace(' ', '_').replace('-', '_') # Sanitize special characters
            node_id = node['id']
            # Convert property list to dict
            props_dict = {p['key']: p['value'] for p in node['properties']}
            props_dict['id'] = node_id  # Ensure id is set as a property
            
            # Write node via Cypher
            query = f"MERGE (n:{label} {{id: $id}}) SET n += $props"
            session.run(query, id=node_id, props=props_dict)

        print("🔗 Importing relationships (edges)...")
        for edge in kg_data['edges']:
            rel_type = edge['type'].replace(' ', '_').replace('-', '_').upper()
            source_id = edge['source']
            target_id = edge['target']
            
            query = f"""
            MATCH (source {{id: $source_id}})
            MATCH (target {{id: $target_id}})
            MERGE (source)-[r:{rel_type}]->(target)
            """
            session.run(query, source_id=source_id, target_id=target_id)
            
    driver.close()
    print("🎉 Graph data successfully imported into Neo4j!")

# ==========================================
# 4. Main entry point
# ==========================================
if __name__ == "__main__":
    import sys
    
    # Support passing the document path via command line
    if len(sys.argv) > 1:
        md_file_path = sys.argv[1]
    else:
        # Default to the test document
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        md_file_path = os.path.join(BASE_DIR, "mock_data", "ecs_product_info.md")
    
    if not os.path.exists(md_file_path):
        print(f"❌ File not found: {md_file_path}")
        sys.exit(1)
        
    try:
        # 1. Run LLM extraction
        kg_data = extract_knowledge_graph(md_file_path)
        
        # 2. Import into Neo4j
        import_to_neo4j(kg_data)
    except Exception as e:
        print(f"❌ Execution failed: {e}")
