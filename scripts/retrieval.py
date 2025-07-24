import os
from langchain.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from .config import gemini_api_key, FAISS_INDEX_PATH
import concurrent.futures

# === Setup ===
from dotenv import load_dotenv
load_dotenv()

def retrieve_multiple_queries(queries, retriever, max_workers=4):
    """Retrieve relevant documents for multiple queries in parallel."""
    def retrieve(q):
        return retriever.get_relevant_documents(q) 

    all_docs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(retrieve, queries)

    for doc_list in results:
        all_docs.extend(doc_list)

    # Remove duplicates while preserving order
    seen = set()
    unique_docs = []
    for doc in all_docs:
        # Create a simple hash based on content and metadata
        doc_hash = hash(doc.page_content + str(doc.metadata))
        if doc_hash not in seen:
            seen.add(doc_hash)
            unique_docs.append(doc)

    return unique_docs

# Load FAISS index from disk
def load_faiss_index(index_path=None):
    """Load FAISS index from disk"""
    if index_path is None:
        index_path = FAISS_INDEX_PATH
    
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"Index path not found: {index_path}. Please run indexing first.")
    
    try:
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=gemini_api_key
        )
        return FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
    except Exception as e:
        raise RuntimeError(f"Failed to load FAISS index: {str(e)}")

# Get retriever object from FAISS index
def get_retriever(index_path=None, k=5):
    """Get a retriever object from the FAISS index."""
    try:
        vectorstore = load_faiss_index(index_path)
        return vectorstore.as_retriever(search_kwargs={"k": k})
    except Exception as e:
        raise RuntimeError(f"Failed to create retriever: {str(e)}")

# Perform semantic search
def retrieve_chunks(query: str, k: int = 5, index_path=None):
    """Retrieve chunks using similarity search"""
    try:
        index = load_faiss_index(index_path)
        docs = index.similarity_search(query, k=k)
        return docs
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve chunks: {str(e)}")