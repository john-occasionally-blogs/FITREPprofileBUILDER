from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.services.fitrep_extractor import FitrepExtractor
from typing import List
import shutil
import os
import tempfile

app = FastAPI(
    title="FITREP PDF Processor",
    description="Service for extracting data from Marine Corps FITREP PDF files",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

extractor = FitrepExtractor()

@app.get("/")
async def root():
    return {"message": "FITREP PDF Processor", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/extract-fitrep")
async def extract_fitrep_data(file: UploadFile = File(...)):
    """
    Extract FITREP data from uploaded PDF file.
    
    Returns:
        Dictionary containing extracted FITREP data including:
        - Administrative information
        - Trait scores (A-H for each of 14 traits)
        - Reporting senior and reviewing officer info
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        shutil.copyfileobj(file.file, tmp_file)
        tmp_path = tmp_file.name
    
    try:
        # Extract data from PDF
        extracted_data = await extractor.extract_fitrep_data(tmp_path)
        return {
            "filename": file.filename,
            "status": "success",
            "data": extracted_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    finally:
        # Clean up temporary file
        os.unlink(tmp_path)

@app.post("/extract-batch")
async def extract_batch_fitreports(files: List[UploadFile] = File(...)):
    """
    Extract FITREP data from multiple PDF files.
    
    Returns:
        List of extraction results for each file.
    """
    results = []
    
    for file in files:
        try:
            if not file.filename.lower().endswith('.pdf'):
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": "File must be a PDF"
                })
                continue
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                shutil.copyfileobj(file.file, tmp_file)
                tmp_path = tmp_file.name
            
            try:
                # Extract data from PDF
                extracted_data = await extractor.extract_fitrep_data(tmp_path)
                results.append({
                    "filename": file.filename,
                    "status": "success",
                    "data": extracted_data
                })
            finally:
                # Clean up temporary file
                os.unlink(tmp_path)
                
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error", 
                "error": str(e)
            })
    
    return {
        "total_files": len(files),
        "successful": len([r for r in results if r["status"] == "success"]),
        "failed": len([r for r in results if r["status"] == "error"]),
        "results": results
    }