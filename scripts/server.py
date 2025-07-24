from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from uuid import uuid4
from pathlib import Path
import shutil
import os
import traceback
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import your modules - using absolute imports
try:
    from scripts.config import gemini_api_key, google_api_key
    from scripts.generation import generate_answer
    from scripts.retrieval import get_retriever
    from scripts.indexing import index_documents
    from scripts.query_expansion import expand_query
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all required modules are in the scripts directory")
    raise

# psyRAG - A Retrieval-Augmented Generation (RAG) system for psychology research
app = FastAPI(title="PsyRAG", description="Psychology RAG System")

# Setup directories
BASE_DIR = Path(__file__).parent  # This is the scripts/ directory
UPLOAD_DIR = BASE_DIR / "uploads"
FRONTEND_DIR = BASE_DIR.parent / "frontend"  # This correctly points to ../frontend/

UPLOAD_DIR.mkdir(exist_ok=True)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files from frontend directory
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# In-memory stores
DOCUMENTS = {}
QUERY_HISTORY = []
CURRENT_RETRIEVER = None  # Store current retriever to avoid recreation

# Schemas
class IndexRequest(BaseModel):
    document_ids: list[str]
    chunk_size: int = 800
    chunk_overlap: int = 150

class QueryRequest(BaseModel):
    query: str
    expand_query: bool = True
    k: int = 5

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serves the main UI page from frontend folder"""
    try:
        return FileResponse(FRONTEND_DIR / "index.html")
    except Exception as e:
        return HTMLResponse(f"<h1>Error loading UI: {str(e)}</h1>", status_code=500)

@app.get("/documents")
async def get_documents():
    """Returns the list of uploaded documents"""
    return {"documents": list(DOCUMENTS.values())}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Uploads a new document"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    file_id = str(uuid4())
    file_path = UPLOAD_DIR / f"{file_id}.pdf"
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        DOCUMENTS[file_id] = {
            "id": file_id,
            "filename": file.filename,
            "path": str(file_path),
            "uploaded_at": datetime.datetime.now().isoformat(),
            "indexed": False,
            "status": "uploaded"
        }
        return {"id": file_id, "filename": file.filename, "message": "File uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Deletes a document"""
    global CURRENT_RETRIEVER
    doc = DOCUMENTS.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        if os.path.exists(doc["path"]):
            os.remove(doc["path"])
    except Exception as e:
        print(f"Error deleting file: {e}")
    
    del DOCUMENTS[doc_id]
    # Reset retriever since documents changed
    CURRENT_RETRIEVER = None
    return {"status": "deleted", "message": "Document deleted successfully"}

@app.post("/index")
async def start_indexing(req: IndexRequest):
    """Index selected documents with user-specified chunk parameters"""
    global CURRENT_RETRIEVER
    
    if not req.document_ids:
        raise HTTPException(status_code=400, detail="No documents selected")
    
    # Validate document IDs
    missing_docs = [doc_id for doc_id in req.document_ids if doc_id not in DOCUMENTS]
    if missing_docs:
        raise HTTPException(status_code=404, detail=f"Documents not found: {missing_docs}")
    
    selected_docs = [DOCUMENTS[doc_id]["path"] for doc_id in req.document_ids]
    print(f"📂 Files to index: {selected_docs}")
    print(f"🔧 Chunk size: {req.chunk_size}, Overlap: {req.chunk_overlap}")
    
    try:
        # Pass the user-specified parameters to indexing
        index_documents(
            selected_docs,
            chunk_size=req.chunk_size,
            chunk_overlap=req.chunk_overlap
        )
        
        # Update document status
        for doc_id in req.document_ids:
            DOCUMENTS[doc_id]["indexed"] = True
            DOCUMENTS[doc_id]["status"] = "indexed"
        
        # Reset retriever to pick up new index
        CURRENT_RETRIEVER = None
        
        return {"message": "Indexing completed successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Indexing error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

@app.post("/query")
async def handle_query(req: QueryRequest):
    """Process a query using the RAG system with user-specified parameters"""
    global CURRENT_RETRIEVER
    
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        # Get retriever with the user-specified k value
        if CURRENT_RETRIEVER is None:
            CURRENT_RETRIEVER = get_retriever(k=req.k)
        else:
            # Update the existing retriever's k value
            CURRENT_RETRIEVER.search_kwargs = {"k": req.k}
        
        print(f"Query: {req.query}")
        print(f"Parameters: expand={req.expand_query}, k={req.k}")
        
        # Generate answer with user parameters
        answer, expanded_queries = generate_answer(
            req.query,
            retriever=CURRENT_RETRIEVER,
            expand=req.expand_query,
            return_expanded=True,
            k=req.k
        )
        
        # Save to history
        history_entry = {
            "query": req.query,
            "answer": answer,
            "expanded_queries": expanded_queries,
            "expand_used": req.expand_query,
            "k_value": req.k,
            "timestamp": datetime.datetime.now().isoformat()
        }
        QUERY_HISTORY.append(history_entry)
        
        return {
            "query": req.query,
            "answer": answer,
            "expanded_queries": expanded_queries
        }
        
    except Exception as e:
        print(f"Query error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@app.get("/query/history")
async def get_query_history():
    """Retrieve the list of past queries"""
    return {"history": QUERY_HISTORY}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "PsyRAG is running"}

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("scripts.server:app", host="0.0.0.0", port=8000, reload=True)