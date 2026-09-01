import os
import sys
import argparse
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_milvus import Milvus
from pymilvus import connections

# ==============================================================================
# Fix compatibility issue between pymilvus 2.6.x and langchain-milvus 0.3.x
# (ConnectionNotExistException caused by MilvusClient connections not being
#  registered with the connections module)
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

# ==============================================================================
# Environment configuration
# ==============================================================================
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

# Load and validate configuration
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("BASE_URL") or None
milvus_host = os.getenv("MILVUS_HOST", "localhost")
milvus_port = os.getenv("MILVUS_PORT", "19530")

if not api_key:
    raise ValueError("❌ OPENAI_API_KEY not found in environment variables")

# Initialize the embedding model (OpenAI text-embedding-3-small, 1536 dims)
embeddings = OpenAIEmbeddings(
    api_key=api_key,
    model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
)

# Milvus connection configuration
MILVUS_URI = f"http://{milvus_host}:{milvus_port}"
COLLECTION_NAME = "cloud_product_docs"

# ==============================================================================
# Core class: Milvus RAG Manager
# ==============================================================================
class MilvusRAGManager:
    def __init__(self):
        self.vector_store = None
        self._init_or_connect()

    def _init_or_connect(self):
        """Connect to an existing Milvus collection; the collection is created automatically on first use if it does not exist."""
        print(f"🔌 Connecting to Milvus vector database: {MILVUS_URI}")
        
        self.vector_store = Milvus(
            embedding_function=embeddings,
            connection_args={"uri": MILVUS_URI},
            collection_name=COLLECTION_NAME,
            auto_id=True,
            drop_old=False # Do not drop existing data by default; enables incremental updates
        )

    def ingest_documents(self, data_dir: str):
        """
        Load all Markdown documents from a directory, split them into chunks, and store them in Milvus.
        """
        if not os.path.exists(data_dir):
            print(f"❌ Directory does not exist: {data_dir}")
            return

        print(f"📂 Loading Markdown documents from directory: {data_dir}")
        # 1. Load documents
        loader = DirectoryLoader(data_dir, glob="*.md", loader_cls=TextLoader, loader_kwargs={'encoding': 'utf-8'})
        documents = loader.load()
        print(f"✅ Successfully loaded {len(documents)} document(s).")

        # 2. Text chunking
        # Use recursive character splitter to preserve contextual coherence
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,       # Vector retrieval chunks are typically smaller than KG chunks to improve precision
            chunk_overlap=50,
            separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""]
        )
        docs = text_splitter.split_documents(documents)
        print(f"🔪 Document split into {len(docs)} chunks.")

        # 3. Write to Milvus (compute embeddings and store)
        print(f"🧠 Computing embeddings and writing to Milvus (collection: {COLLECTION_NAME})...")
        
        # Incremental import: automatically handles embedding computation and index creation
        Milvus.from_documents(
            docs, 
            embeddings, 
            connection_args={"uri": MILVUS_URI}, 
            collection_name=COLLECTION_NAME, 
            drop_old=True # Overwrite existing collection to keep data clean; set to False for incremental updates
        )
        print(f"🎉 Successfully ingested {len(docs)} vectors!")

    def query(self, question: str, top_k: int = 3):
        """
        Perform a vector similarity search in Milvus based on the user's question.
        """
        print(f"🔍 Searching for: '{question}'")
        
        # Execute similarity search
        results = self.vector_store.similarity_search_with_score(question, k=top_k)
        
        if not results:
            print("⚠️ No relevant document chunks found.")
            return []

        print(f"\n✅ Found {len(results)} relevant chunk(s):")
        formatted_results = []
        for i, (doc, score) in enumerate(results):
            # In LangChain's Milvus implementation, score is typically distance (lower = more similar), depending on metric_type
            source = doc.metadata.get('source', 'Unknown')
            filename = os.path.basename(source)
            content = doc.page_content.strip()
            
            print(f"\n--- [Chunk {i+1}] Source: {filename} (relevance score: {score:.4f}) ---")
            print(f"{content[:200]}...") # Preview first 200 characters
            
            formatted_results.append({
                "content": content,
                "source": filename,
                "score": score
            })
            
        return formatted_results

# ==============================================================================
# Direct execution entry point
# ==============================================================================
def main():
    # Instantiate the RAG manager
    manager = MilvusRAGManager()
    
    # 1. To ingest documents, uncomment the two lines below
    # BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # manager.ingest_documents(os.path.join(BASE_DIR, "mock_data"))
    
    # 2. Hard-code the test question here
    test_question = "What are the restrictions for a 5-day no-questions-asked refund?"
    
    # Run the query
    manager.query(test_question, top_k=3)

if __name__ == "__main__":
    main()