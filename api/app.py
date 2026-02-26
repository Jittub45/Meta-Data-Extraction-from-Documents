"""
FastAPI REST API
Wraps the extraction system as a web service
"""

import os
import shutil
import tempfile
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse

from src.text_extractor import extract_text
from src.prompt_builder import build_extraction_prompt
from src.llm_client import LLMClient
from src.post_processor import post_process

app = FastAPI(
    title="Document Metadata Extractor",
    description="AI-powered metadata extraction from rental agreements",
    version="1.0.0"
)

# Initialize LLM client on startup
llm_client = None

@app.on_event("startup")
async def startup():
    global llm_client
    llm_client = LLMClient()

@app.get("/")
async def root():
    return {"message": "Document Metadata Extractor API", "status": "running"}

@app.post("/extract")
async def extract_metadata(file: UploadFile = File(...)):
    """
    Upload a .docx or .png file and extract metadata
    
    Returns JSON with:
    - agreement_value
    - agreement_start_date
    - agreement_end_date
    - renewal_notice_days
    - party_one
    - party_two
    """
    
    # Save uploaded file temporarily
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)
    
    try:
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Step 1: Extract text
        text = extract_text(temp_path)
        
        if not text:
            return JSONResponse(
                status_code=400,
                content={"error": "Could not extract text from document"}
            )
        
        # Step 2: Build prompt
        prompt = build_extraction_prompt(text)
        
        # Step 3: Get metadata from LLM
        raw_metadata = llm_client.extract_metadata(prompt)
        
        # Step 4: Post-process
        cleaned = post_process(raw_metadata)
        
        return {
            "filename": file.filename,
            "metadata": cleaned,
            "status": "success"
        }
    
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.get("/health")
async def health():
    return {"status": "healthy"}