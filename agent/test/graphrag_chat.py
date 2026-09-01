import os
import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_neo4j import Neo4jGraph as NewNeo4jGraph
from langchain_neo4j import GraphCypherQAChain
from langchain_core.prompts import PromptTemplate

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

def setup_graphrag():
    """
    Initialize the Neo4j graph database connection and LLM, then build the GraphRAG QA Chain.
    """
    print("🔌 Connecting to Neo4j database...")
    try:
        graph = NewNeo4jGraph(
            url=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            username=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "password")
        )
        # Refresh the graph schema so the LLM knows what nodes and relationships exist
        graph.refresh_schema()
        print("✅ Neo4j connected successfully! Graph schema loaded.")
    except Exception as e:
        print(f"❌ Neo4j connection failed, please check database status and configuration: {e}")
        sys.exit(1)

    print("🧠 Initializing OpenAI LLM...")
    llm = ChatOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("MODEL", "gpt-4o"),
        base_url=os.getenv("BASE_URL") or None,
        temperature=0,
    )

    # ========================================================
    # Enhanced Cypher generation prompt
    # This is critical — it guides the LLM to use the correct syntax for the cloud product graph.
    # ========================================================
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
   To query properties of a specific model (e.g. vCPU, memory, eni_count, network_bandwidth), query the InstanceType node and look up properties there.
   To query the description of an entire instance family, query the InstanceTypeFamily node.
4. Return format: return as much detail as possible; when returning nodes use RETURN node, not just the ID.

The question is:
{question}"""

    cypher_prompt = PromptTemplate(
        template=CYPHER_GENERATION_TEMPLATE,
        input_variables=["schema", "question"]
    )

    # Core: GraphCypherQAChain
    # Pipeline: natural language -> LLM generates Cypher -> Neo4j executes -> LLM converts result to natural language answer
    chain = GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph,
        cypher_prompt=cypher_prompt, # Inject the specialized prompt we crafted above
        verbose=True, # Enable verbose logging to see generated Cypher statements
        return_intermediate_steps=True, # Return intermediate steps (generated query and graph results)
        allow_dangerous_requests=True, # Allow query execution
    )
    
    return chain

def chat_with_graph():
    """
    Interactive command-line Q&A session.
    """
    chain = setup_graphrag()
    
    print("\n" + "="*50)
    print("🤖 GraphRAG intelligent assistant is ready!")
    print("You can ask questions about cloud products in natural language, for example:")
    print("- Which preemptible instances are supported in the Beijing region?")
    print("- How many elastic network interfaces can a g8a instance attach at most?")
    print("- Which instances do not support local NVMe SSD?")
    print("Type 'exit' or 'quit' to quit.")
    print("="*50 + "\n")

    while True:
        question = input("🧑 Your question: ")
        if question.lower() in ['exit', 'quit']:
            print("👋 Goodbye!")
            break
        if not question.strip():
            continue

        try:
            print("⏳ Thinking and querying the knowledge graph...\n")
            result = chain.invoke({"query": question})
            print(f"\n🤖 Answer:\n{result['result']}\n")
        except Exception as e:
            print(f"\n❌ Query error: {e}\n")

if __name__ == "__main__":
    chat_with_graph()