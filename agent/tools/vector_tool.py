import os
import json
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_milvus import Milvus
from pymilvus import connections
from langchain_core.tools import tool

# ==============================================================================
# Fix compatibility issue between pymilvus 2.6.x and langchain-milvus 0.3.x
# ==============================================================================
original_fetch = connections._fetch_handler
def patched_fetch(alias):
    try:
        return original_fetch(alias)
    except Exception:
        from pymilvus.client.connection_manager import ConnectionManager
        mgr = ConnectionManager.get_instance()
        for mc in mgr._registry.values():
            if f"cm-{id(mc.handler)}" == alias:
                return mc.handler
        for mc in mgr._dedicated.values():
            if f"cm-{id(mc.handler)}" == alias:
                return mc.handler
        raise
connections._fetch_handler = patched_fetch
# ==============================================================================

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

_milvus_instance = None

def _get_milvus_store():
    global _milvus_instance
    if _milvus_instance is not None:
        return _milvus_instance

    api_key = os.getenv("OPENAI_API_KEY")
    milvus_host = os.getenv("MILVUS_HOST", "localhost")
    milvus_port = os.getenv("MILVUS_PORT", "19530")
    milvus_uri = f"http://{milvus_host}:{milvus_port}"

    print(f"🔌 [Init] Connecting to Milvus vector database: {milvus_uri}")
    embeddings = OpenAIEmbeddings(
        api_key=api_key,
        model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
    )

    _milvus_instance = Milvus(
        embedding_function=embeddings,
        connection_args={"uri": milvus_uri},
        collection_name="cloud_product_docs",
        auto_id=True,
        drop_old=False
    )
    return _milvus_instance

@tool
def query_vector_db(query: str) -> str:
    """
    Query cloud product documentation via semantic search (RAG).
    Use this tool when the user asks about concepts, step-by-step procedures, or detailed rules (e.g., refund policies, what is a VPC, how to create an instance).
    """
    try:
        # ================== TODO 20 - RAG retrieval tool ==================
        # GOAL : Search the product docs and format the hits for the LLM.
        # WHY  : How you FORMAT retrieved chunks drives citation quality as much as the search does.
        # STEPS:
        #   1. store = _get_milvus_store(); results = store.similarity_search_with_score(query, k=3).
        #   2. If results is empty, return a plain 'no information found' string.
        #   3. For each (doc, score): take os.path.basename(doc.metadata.get('source','Unknown')).
        #   4. Format each as '[Source: <file>]\n<content>' and join with a blank line.
        # HINT : Returning the source filename is what lets the agent cite 'Vector search: xxx.md'.
        # CHECK: Ask 'what is the refund policy' - the answer should name its source file.
        # SIZE : ~9 lines
        raise NotImplementedError("TODO 20: search Milvus and format results")
        # ======================================================
    except Exception as e:
        return f"Error querying vector database: {str(e)}"
