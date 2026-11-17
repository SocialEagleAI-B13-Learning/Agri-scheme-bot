import os
import shutil
import sys
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.rag_engine import ask_scheme_question

app = FastAPI(
    title="Agricultural Scheme RAG API",
    description="Backend API for querying government agricultural schemes with exact PDF & page citations.",
    version="1.0.0"
)

# Enable CORS so your Streamlit frontend can talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str

@app.get("/")
def home():
    return {"status": "Online", "message": "Welcome to the Agri-Scheme RAG API!"}

@app.post("/ask")
def ask_question(request: QuestionRequest):
    """Endpoint for asking questions about agricultural schemes."""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    
    try:
        result = ask_scheme_question(request.question)
        return {
            "success": True,
            "question": request.question,
            "answer": result["answer"],
            "sources": result["sources"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Endpoint to upload a new scheme PDF dynamically and rebuild the FAISS index."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    pdfs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "pdfs"))
    os.makedirs(pdfs_dir, exist_ok=True)
    
    file_path = os.path.join(pdfs_dir, file.filename)
    
    try:
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Import ingestion locally inside the function to avoid startup circular imports
        from ingest import build_vector_database
        build_vector_database()
        
        return {
            "success": True,
            "message": f"Successfully uploaded '{file.filename}' and updated FAISS index!"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process upload: {str(e)}")