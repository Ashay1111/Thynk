from fastapi import FastAPI, File, UploadFile, Request, HTTPException, Cookie
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
from typing import Optional

# Load environment variables
load_dotenv()

# Import your modules
try:
    from scripts.config import gemini_api_key, google_api_key
    from scripts.generation import generate_answer
    from scripts.retrieval import get_retriever
    from scripts.indexing import index_documents
    from scripts.query_expansion import expand_query
except ImportError as e:
    print(f"Import error: {e}")
    raise

app = FastAPI(title="PsyRAG", description="Psychology RAG System")

# Setup directories
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
FRONTEND_DIR = BASE_DIR.parent / "frontend"

UPLOAD_DIR.mkdir(exist_ok=True)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# Multi-user storage - organized by session
USER_SESSIONS = {}  # session_id -> user data

class UserSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.documents = {}
        self.query_history = []
        self.current_retriever = None
        self.upload_dir = UPLOAD_DIR / session_id
        self.index_dir = BASE_DIR / "data" / session_id / "faiss_index"
        
        # Create user-specific directories
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)

def get_session_id(request: Request) -> str:
    """Get or create session ID from cookie"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid4())
    return session_id

def get_user_session(session_id: str) -> UserSession:
    """Get or create user session"""
    if session_id not in USER_SESSIONS:
        USER_SESSIONS[session_id] = UserSession(session_id)
    return USER_SESSIONS[session_id]

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
async def serve_ui(request: Request):
    """Serves the main UI page with session cookie"""
    try:
        response = FileResponse(FRONTEND_DIR / "index.html")
        session_id = get_session_id(request)
        response.set_cookie("session_id", session_id, max_age=86400*30)  # 30 days
        return response
    except Exception as e:
        return HTMLResponse(f"<h1>Error loading UI: {str(e)}</h1>", status_code=500)

@app.get("/documents")
async def get_documents(request: Request):
    """Returns the list of uploaded documents for the current session"""
    session_id = get_session_id(request)
    user_session = get_user_session(session_id)
    return {"documents": list(user_session.documents.values())}

@app.post("/upload")
async def upload_document(request: Request, file: UploadFile = File(...)):
    """Uploads a new document for the current session"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    session_id = get_session_id(request)
    user_session = get_user_session(session_id)
    
    file_id = str(uuid4())
    file_path = user_session.upload_dir / f"{file_id}.pdf"
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        user_session.documents[file_id] = {
            "id": file_id,
            "filename": file.filename,
            "path": str(file_path),
            "uploaded_at": datetime.datetime.now().isoformat(),
            "indexed": False,
            "status": "uploaded"
        }
        
        response = JSONResponse({"id": file_id, "filename": file.filename, "message": "File uploaded successfully"})
        response.set_cookie("session_id", session_id, max_age=86400*30)
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.delete("/documents/{doc_id}")
async def delete_document(request: Request, doc_id: str):
    """Deletes a document for the current session"""
    session_id = get_session_id(request)
    user_session = get_user_session(session_id)
    
    doc = user_session.documents.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        if os.path.exists(doc["path"]):
            os.remove(doc["path"])
    except Exception as e:
        print(f"Error deleting file: {e}")
    
    del user_session.documents[doc_id]
    # Reset retriever since documents changed
    user_session.current_retriever = None
    return {"status": "deleted", "message": "Document deleted successfully"}

@app.post("/index")
async def start_indexing(request: Request, req: IndexRequest):
    """Index selected documents for the current session"""
    session_id = get_session_id(request)
    user_session = get_user_session(session_id)
    
    if not req.document_ids:
        raise HTTPException(status_code=400, detail="No documents selected")
    
    # Validate document IDs
    missing_docs = [doc_id for doc_id in req.document_ids if doc_id not in user_session.documents]
    if missing_docs:
        raise HTTPException(status_code=404, detail=f"Documents not found: {missing_docs}")
    
    selected_docs = [user_session.documents[doc_id]["path"] for doc_id in req.document_ids]
    print(f"📂 Files to index for session {session_id}: {selected_docs}")
    print(f"🔧 Chunk size: {req.chunk_size}, Overlap: {req.chunk_overlap}")
    
    try:
        # Use session-specific index directory
        from scripts.indexing import load_files, chunk_documents, embed_documents
        
        # Load and process documents
        docs = load_files(selected_docs)
        if not docs:
            raise ValueError("No documents loaded from provided file paths.")
        
        chunks = chunk_documents(docs, chunk_size=req.chunk_size, chunk_overlap=req.chunk_overlap)
        if not chunks:
            raise ValueError("Chunking resulted in zero chunks.")
        
        # Save to session-specific index
        embed_documents(chunks, save_path=user_session.index_dir)
        
        # Update document status
        for doc_id in req.document_ids:
            user_session.documents[doc_id]["indexed"] = True
            user_session.documents[doc_id]["status"] = "indexed"
        
        # Reset retriever to pick up new index
        user_session.current_retriever = None
        
        return {"message": "Indexing completed successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Indexing error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

@app.post("/query")
async def handle_query(request: Request, req: QueryRequest):
    """Process a query for the current session"""
    session_id = get_session_id(request)
    user_session = get_user_session(session_id)
    
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        # Get retriever with user's specific index
        if user_session.current_retriever is None:
            from scripts.retrieval import get_retriever
            user_session.current_retriever = get_retriever(
                index_path=user_session.index_dir, 
                k=req.k
            )
        else:
            # Update the existing retriever's k value
            user_session.current_retriever.search_kwargs = {"k": req.k}
        
        print(f"Query for session {session_id}: {req.query}")
        print(f"Parameters: expand={req.expand_query}, k={req.k}")
        
        # Generate answer with user parameters
        answer, expanded_queries = generate_answer(
            req.query,
            retriever=user_session.current_retriever,
            expand=req.expand_query,
            return_expanded=True,
            k=req.k
        )
        
        # Save to user's history
        history_entry = {
            "query": req.query,
            "answer": answer,
            "expanded_queries": expanded_queries,
            "expand_used": req.expand_query,
            "k_value": req.k,
            "timestamp": datetime.datetime.now().isoformat()
        }
        user_session.query_history.append(history_entry)
        
        return {
            "query": req.query,
            "answer": answer,
            "expanded_queries": expanded_queries
        }
        
    except Exception as e:
        print(f"Query error for session {session_id}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@app.get("/query/history")
async def get_query_history(request: Request):
    """Retrieve the list of past queries for the current session"""
    session_id = get_session_id(request)
    user_session = get_user_session(session_id)
    return {"history": user_session.query_history}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "PsyRAG is running"}

# Clean up old sessions periodically (optional)
@app.on_event("startup")
async def cleanup_old_sessions():
    """Clean up old session data on startup"""
    import asyncio
    
    async def periodic_cleanup():
        while True:
            # Wait 24 hours between cleanups
            await asyncio.sleep(86400)
            
            # Remove sessions older than 7 days
            cutoff = datetime.datetime.now() - datetime.timedelta(days=7)
            sessions_to_remove = []
            
            for session_id, session in USER_SESSIONS.items():
                # Check if session has any recent activity
                if (session.query_history and 
                    datetime.datetime.fromisoformat(session.query_history[-1]["timestamp"]) < cutoff):
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                try:
                    session = USER_SESSIONS[session_id]
                    # Clean up files
                    if session.upload_dir.exists():
                        shutil.rmtree(session.upload_dir)
                    if session.index_dir.exists():
                        shutil.rmtree(session.index_dir)
                    del USER_SESSIONS[session_id]
                    print(f"Cleaned up old session: {session_id}")
                except Exception as e:
                    print(f"Error cleaning up session {session_id}: {e}")
    
    # Start cleanup task
    asyncio.create_task(periodic_cleanup())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("scripts.server:app", host="0.0.0.0", port=8000, reload=True)