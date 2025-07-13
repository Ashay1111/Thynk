import os
from langchain.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config import FAISS_INDEX_PATH

def load_files(file_paths: list[str]) -> list:
    docs = []
    for file_path in file_paths:
        filename = os.path.basename(file_path)
        print(f"Loading: {filename}")  # Fixed: moved filename definition before usage
        if not filename.lower().endswith(".pdf"):
            continue
        try:
            loader = PyMuPDFLoader(file_path)
            loaded_docs = loader.load()
            for doc in loaded_docs:
                doc.metadata.update({
                    "filename": filename
                })
            docs.extend(loaded_docs)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
    return docs

def chunk_documents(docs, chunk_size=800, chunk_overlap=150):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_documents(docs)

def embed_documents(chunks, save_path=FAISS_INDEX_PATH):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    try:
        db = FAISS.from_documents(chunks, embedding=embeddings)
    except Exception as e:
        print("Embedding or FAISS error:", e)
        raise

    db.save_local(save_path)
    print(f"FAISS index saved to: {save_path}")

def index_documents(file_paths, chunk_size=800, chunk_overlap=150):
    print("Loading documents...")
    docs = load_files(file_paths)
    if not docs:
        raise ValueError("No documents loaded from provided file paths.")

    print(f"Loaded {len(docs)} docs.")

    print("Chunking...")
    chunks = chunk_documents(docs, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    print(f"Generated {len(chunks)} chunks.")

    if not chunks:
        raise ValueError("Chunking resulted in zero chunks. Check document content.")

    print("🔐 Embedding and indexing...")
    embed_documents(chunks)
    print("Indexing complete.")