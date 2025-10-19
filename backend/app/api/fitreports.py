from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.models import Officer, FitReport, TraitScore, RelativeValue
from app.utils.scoring import calculate_fra_score, calculate_relative_values, TRAIT_NAMES
from app.utils.rs_list_parser import parse_rs_list_pdf, generate_trait_scores_from_fra, generate_dummy_fitrep_id
from typing import List, Optional, Dict
from pydantic import BaseModel
import httpx
import os
from datetime import datetime
from decimal import Decimal
import tempfile
import shutil

router = APIRouter()

class FitReportResponse(BaseModel):
    id: int
    officer_id: int
    fitrep_id: str
    rank_at_time: str
    period_from: str
    period_to: str
    fra_score: Optional[float]
    relative_value: Optional[int]
    organization: Optional[str]
    reporting_senior_name: Optional[str]

    class Config:
        from_attributes = True

class ProcessFilesRequest(BaseModel):
    officer_id: int

@router.get("/all", response_model=List[FitReportResponse])
async def get_all_fitreports(db: Session = Depends(get_db)):
    """Get all FITREPs across all officers."""
    fitreports = db.query(FitReport).all()

    # Get relative values for each report
    response_data = []
    for report in fitreports:
        rv_data = db.query(RelativeValue).filter(RelativeValue.fitrep_id == report.id).first()
        rv_value = rv_data.relative_value if rv_data else None

        response_data.append(FitReportResponse(
            id=report.id,
            officer_id=report.officer_id,
            fitrep_id=report.fitrep_id,
            rank_at_time=report.rank_at_time,
            period_from=str(report.period_from),
            period_to=str(report.period_to),
            fra_score=float(report.fra_score) if report.fra_score else None,
            relative_value=rv_value,
            organization=report.organization,
            reporting_senior_name=report.reporting_senior_name
        ))

    return response_data

@router.get("/officer/{officer_id}", response_model=List[FitReportResponse])
async def get_officer_fitreports(officer_id: int, db: Session = Depends(get_db)):
    """Get all FITREPs for a specific officer."""
    officer = db.query(Officer).filter(Officer.id == officer_id).first()
    if not officer:
        raise HTTPException(status_code=404, detail="Officer not found")

    fitreports = db.query(FitReport).filter(FitReport.officer_id == officer_id).all()

    # Get relative values for each report
    response_data = []
    for report in fitreports:
        rv_data = db.query(RelativeValue).filter(RelativeValue.fitrep_id == report.id).first()
        rv_value = rv_data.relative_value if rv_data else None

        response_data.append(FitReportResponse(
            id=report.id,
            officer_id=report.officer_id,
            fitrep_id=report.fitrep_id,
            rank_at_time=report.rank_at_time,
            period_from=str(report.period_from),
            period_to=str(report.period_to),
            fra_score=float(report.fra_score) if report.fra_score else None,
            relative_value=rv_value,
            organization=report.organization,
            reporting_senior_name=report.reporting_senior_name
        ))

    return response_data

@router.post("/auto-upload")
async def auto_upload_create_profile(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Fully automatic upload: Extract ALL officer info from the first PDF and create profile.
    No manual entry required - everything is extracted from the PDFs automatically.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    print(f"AUTO-UPLOAD: Received {len(files)} files")
    for i, f in enumerate(files):
        print(f"  File {i+1}: {f.filename}, size: {f.size if hasattr(f, 'size') else 'unknown'}")
    
    first_file = files[0]
    try:
        # Reset file pointer for later use
        first_file.file.seek(0)

        # Extract data using PDF processor service
        pdf_processor_url = os.getenv("PDF_PROCESSOR_URL", "http://pdf-processor:8001")

        # Create form data with the file
        files_data = {"file": (first_file.filename, first_file.file, "application/pdf")}

        # Call PDF processor service
        response = httpx.post(f"{pdf_processor_url}/extract-fitrep", files=files_data, timeout=30.0)

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"PDF processor failed: {response.text}")

        result = response.json()
        extracted_data = result.get("data", {})

        if not extracted_data:
            raise HTTPException(status_code=400, detail="Could not extract data from PDF")
        
        # Extract reporting senior info from the PDF data  
        rs_first_name = extracted_data.get('rs_first_name', 'UNKNOWN')
        rs_last_name = extracted_data.get('rs_last_name', 'REPORTING SENIOR') 
        rs_rank = extracted_data.get('rs_rank', 'UNKNOWN')  # Default to UNKNOWN
        rs_edipi = extracted_data.get('rs_edipi')
        
        # Debug: Show what RS data was extracted from FIRST file only
        print(f"  DEBUG RS extraction (FIRST FILE ONLY):")
        print(f"    rs_first_name: {rs_first_name}")
        print(f"    rs_last_name: {rs_last_name}")  
        print(f"    rs_rank: {rs_rank}")
        print(f"    rs_edipi: {rs_edipi}")
        print(f"    All extracted keys: {list(extracted_data.keys())}")
        
        # If extraction failed, use fallback values
        if rs_last_name in ['PROMOTION', 'AUGMENTATION', 'GENERATED'] or rs_first_name in ['PROMOTION', 'AUGMENTATION', 'AUTO']:
            rs_first_name = 'UNKNOWN'
            rs_last_name = 'REPORTING SENIOR'
            rs_rank = 'UNKNOWN'
        
        # Always generate a service number since extraction might not find EDIPI
        timestamp = int(datetime.now().timestamp())
        service_number = rs_edipi if rs_edipi else f"AUTO_{timestamp}"
        
        # Use extracted names if they look valid, otherwise use defaults
        if not rs_first_name or rs_first_name in ['UNKNOWN', 'PROMOTION', 'AUGMENTATION']:
            rs_first_name = "AUTO"
        if not rs_last_name or rs_last_name in ['UNKNOWN', 'PROMOTION', 'AUGMENTATION']:  
            rs_last_name = f"GENERATED_{timestamp}"
        
        # Create officer data
        officer_data = {
            "last_name": rs_last_name.upper(),
            "first_name": rs_first_name.upper(),
            "middle_initial": None,  # Extract this later if needed
            "service_number": service_number,
            "current_rank": rs_rank.upper()
        }
        
        # Check if officer already exists by service number
        existing_officer = db.query(Officer).filter(Officer.service_number == service_number).first()
        if existing_officer:
            # Update existing officer info with extracted data
            for key, value in officer_data.items():
                if value and value not in ['UNKNOWN', 'UPDATE', 'REQUIRED']:
                    setattr(existing_officer, key, value)
            db.commit()
            officer_id = existing_officer.id
        else:
            # Create new officer
            db_officer = Officer(**officer_data)
            db.add(db_officer)
            db.commit()
            db.refresh(db_officer)
            officer_id = db_officer.id
        
        # TODO: Replace with multi-RS logic - for now use single RS
        result = await process_fitrep_files_local(files, officer_id, db)
        result["auto_extracted_info"] = {
            "reporting_senior_name": f"{rs_last_name}, {rs_first_name}",
            "reporting_senior_rank": rs_rank,
            "service_number": service_number,
            "extracted_successfully": rs_first_name != 'UNKNOWN'
        }
        
        return result
        
    except Exception as e:
        import traceback
        error_details = f"{str(e)} | Traceback: {traceback.format_exc()}"
        print(f"AUTO-UPLOAD ERROR: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error in auto upload: {str(e)}")

@router.post("/multi-rs-upload")
async def multi_rs_upload(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Multi-RS Upload: Process each FITREP individually and create separate profiles for each unique Reporting Senior.
    
    This endpoint will:
    1. Extract RS info from each FITREP individually 
    2. Create separate Officer records for each unique RS found
    3. Associate each FITREP with its correct RS
    4. Return list of created RS profiles for selection
    """
    print(f"MULTI-RS-UPLOAD: Processing {len(files)} files")
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    try:
        import tempfile, shutil, os
        from pathlib import Path
        from datetime import datetime

        # Use PDF processor service
        pdf_processor_url = os.getenv("PDF_PROCESSOR_URL", "http://pdf-processor:8001")

        unique_rs_officers = {}  # {rs_key: officer_id}
        fitrep_assignments = []  # List of (file_data, rs_officer_id) tuples
        extraction_failures = []  # Track files that fail during extraction

        print("Step 1: Extracting RS data from each FITREP...")

        # Process each FITREP to extract RS data and build unique RS list
        for file_idx, file in enumerate(files):
            try:
                # Reset file pointer
                file.file.seek(0)

                # Call PDF processor service
                files_data = {"file": (file.filename, file.file, "application/pdf")}
                response = httpx.post(f"{pdf_processor_url}/extract-fitrep", files=files_data, timeout=30.0)

                if response.status_code != 200:
                    print(f"  File {file_idx + 1}: PDF processor failed: {response.text}")
                    extraction_failures.append({
                        'filename': file.filename,
                        'status': 'failed',
                        'message': f'PDF extraction failed: {response.text[:100]}'
                    })
                    continue

                result = response.json()
                extracted_data = result.get("data", {})

                if not extracted_data:
                    print(f"  File {file_idx + 1}: No data extracted")
                    extraction_failures.append({
                        'filename': file.filename,
                        'status': 'failed',
                        'message': 'No data could be extracted from PDF'
                    })
                    continue
                
                # Get RS info
                rs_last_name = extracted_data.get('rs_last_name', f'UNKNOWN_RS_{file_idx + 1}')
                rs_edipi = extracted_data.get('rs_edipi')
                rs_first_name = extracted_data.get('rs_first_name', 'AUTO')
                rs_rank = extracted_data.get('rs_rank', 'UNKNOWN')
                marine_name = extracted_data.get('last_name', f'MARINE_{file_idx + 1}')
                
                print(f"  File {file_idx + 1}: Marine={marine_name}, RS={rs_last_name} (EDIPI: {rs_edipi})")
                
                # Create unique RS key
                rs_key = f"{rs_last_name}_{rs_edipi}" if rs_edipi else f"{rs_last_name}_{file_idx}"
                
                # Create RS Officer record if not exists
                if rs_key not in unique_rs_officers:
                    timestamp = int(datetime.now().timestamp()) + file_idx
                    service_number = rs_edipi if rs_edipi else f"AUTO_{timestamp}"
                    
                    officer_data = {
                        "last_name": rs_last_name.upper(),
                        "first_name": rs_first_name.upper() if rs_first_name != 'UNKNOWN' else 'AUTO',
                        "middle_initial": None,
                        "service_number": service_number,
                        "current_rank": rs_rank.upper() if rs_rank != 'UNKNOWN' else 'UNKNOWN'
                    }
                    
                    # Check if RS already exists
                    existing_officer = db.query(Officer).filter(Officer.service_number == service_number).first()
                    if existing_officer:
                        unique_rs_officers[rs_key] = existing_officer.id
                        print(f"    Found existing RS: {existing_officer.last_name} (ID: {existing_officer.id})")
                    else:
                        # Create new RS Officer
                        db_officer = Officer(**officer_data)
                        db.add(db_officer)
                        db.commit()
                        db.refresh(db_officer)
                        unique_rs_officers[rs_key] = db_officer.id
                        print(f"    Created new RS: {db_officer.last_name} (ID: {db_officer.id})")
                
                # Store assignment for FITREP processing
                fitrep_assignments.append({
                    'file': file,
                    'file_idx': file_idx,
                    'extracted_data': extracted_data,
                    'rs_officer_id': unique_rs_officers[rs_key],
                    'rs_name': rs_last_name
                })

            except Exception as e:
                print(f"  File {file_idx + 1}: Error processing - {str(e)}")
                extraction_failures.append({
                    'filename': file.filename,
                    'status': 'failed',
                    'message': f'Extraction error: {str(e)}'
                })
        
        print(f"\\nStep 2: Created {len(unique_rs_officers)} unique RS profiles")
        for rs_key, officer_id in unique_rs_officers.items():
            rs_officer = db.query(Officer).filter(Officer.id == officer_id).first()
            fitrep_count = len([a for a in fitrep_assignments if a['rs_officer_id'] == officer_id])
            print(f"  - {rs_officer.last_name}: {fitrep_count} FITREPs")
        
        print("\\nStep 3: Processing FITREPs with correct RS assignments...")

        # Now process each FITREP with its correct RS assignment
        total_processed = 0
        processing_details = []  # Track detailed results

        for assignment in fitrep_assignments:
            try:
                # Reset file pointer
                assignment['file'].file.seek(0)

                # Process this single FITREP for the correct RS
                result = await process_single_fitrep_for_rs(
                    assignment['file'],
                    assignment['extracted_data'],
                    assignment['rs_officer_id'],
                    assignment['file_idx'],
                    db
                )

                if result == "success":
                    total_processed += 1
                    processing_details.append({
                        'filename': assignment['file'].filename,
                        'status': 'success',
                        'message': f"Processed for RS: {assignment['rs_name']}"
                    })
                    print(f"  ✓ Processed {assignment['file'].filename} for RS: {assignment['rs_name']}")
                elif result == "duplicate":
                    processing_details.append({
                        'filename': assignment['file'].filename,
                        'status': 'skipped',
                        'message': 'Duplicate FITREP ID - already in database'
                    })
                    print(f"  ⚠️ Skipped {assignment['file'].filename} (duplicate FITREP ID)")
                elif result == "non_observed":
                    processing_details.append({
                        'filename': assignment['file'].filename,
                        'status': 'skipped',
                        'message': 'Non-Observed report (all traits marked H)'
                    })
                    print(f"  ⚠️ Skipped {assignment['file'].filename} (Non-Observed report)")
                else:
                    processing_details.append({
                        'filename': assignment['file'].filename,
                        'status': 'failed',
                        'message': f'Unknown result: {result}'
                    })

            except Exception as e:
                processing_details.append({
                    'filename': assignment['file'].filename,
                    'status': 'failed',
                    'message': str(e)
                })
                print(f"  ✗ Error processing {assignment['file'].filename}: {str(e)}")
        
        # Get final profile summary
        profiles_summary = []
        for rs_key, officer_id in unique_rs_officers.items():
            rs_officer = db.query(Officer).filter(Officer.id == officer_id).first()
            fitrep_count = db.query(FitReport).filter(FitReport.officer_id == officer_id).count()
            profiles_summary.append({
                "id": officer_id,
                "name": f"{rs_officer.last_name}, {rs_officer.first_name}",
                "rank": rs_officer.current_rank,
                "fitrep_count": fitrep_count
            })
        
        # Recalculate RV values for all affected reporting seniors
        print("Step 4: Calculating relative values for all RS profiles...")
        await _recalculate_all_relative_values(db)

        # Combine extraction failures with processing details
        all_processing_details = extraction_failures + processing_details

        return {
            "message": f"Successfully created {len(unique_rs_officers)} RS profiles with {total_processed} FITREPs",
            "rs_profiles": profiles_summary,
            "total_files_processed": total_processed,
            "unique_rs_count": len(unique_rs_officers),
            "processing_details": all_processing_details  # Include detailed results from both extraction and processing
        }
        
    except Exception as e:
        print(f"MULTI-RS-UPLOAD ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error in multi-RS upload: {str(e)}")

async def process_single_fitrep_for_rs(
    file: UploadFile,
    extracted_data: dict,
    rs_officer_id: int,
    file_idx: int,
    db: Session
):
    """
    Process a single FITREP for a specific Reporting Senior with correct data mapping.
    """
    try:
        # Get marine info from extracted data
        marine_name = extracted_data.get('last_name', f'MARINE_{file_idx + 1}')
        marine_edipi = extracted_data.get('marine_edipi')
        fitrep_id = extracted_data.get('fitrep_id', f'AUTO_{rs_officer_id}_{file_idx}')
        grade = extracted_data.get('grade', 'UNKNOWN')
        occ = extracted_data.get('occ', 'UNKNOWN')
        to_date = extracted_data.get('to_date')
        
        # Parse dates
        from datetime import datetime
        period_to = None
        if to_date and len(str(to_date)) == 8:
            try:
                period_to = datetime.strptime(str(to_date), '%Y%m%d').date()
            except ValueError:
                pass
        
        # Check for duplicate FITREP ID across ALL officers (not just this RS)
        existing_fitrep = db.query(FitReport).filter(FitReport.fitrep_id == str(fitrep_id)).first()
        if existing_fitrep:
            print(f"  ⚠️  Skipping duplicate FITREP ID: {fitrep_id} (already exists for Officer ID: {existing_fitrep.officer_id})")
            return "duplicate"  # Skip this FITREP
        
        # Get RS name from database for correct display
        rs_officer = db.query(Officer).filter(Officer.id == rs_officer_id).first()
        rs_name = f"{rs_officer.last_name}, {rs_officer.first_name}" if rs_officer else "UNKNOWN RS"
        
        # Create FITREP record with correct data
        fitrep_data = {
            "officer_id": rs_officer_id,  # This is the RS, not the Marine
            "fitrep_id": str(fitrep_id),
            "report_date": period_to,  # Report date is the same as period end date
            "period_to": period_to,
            "rank_at_time": grade,
            "occasion_type": occ,
            "reporting_senior_name": rs_name,  # Correct RS name
            "organization": f"Marine: {marine_name}",  # Store marine name in organization field for reference
        }
        
        # Calculate FRA score using proper letter grade system with H handling
        page2_values = extracted_data.get('page2_values', [4] * 5)
        page3_values = extracted_data.get('page3_values', [4] * 5)
        page4_values = extracted_data.get('page4_values', [4] * 4)
        
        def score_to_letter(score):
            # Convert numeric checkbox values (1-8) to letter grades (A-H)
            # Based on FITREP checkbox positions: A=1, B=2, C=3, D=4, E=5, F=6, G=7, H=8
            mapping = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F', 7: 'G', 8: 'H'}
            return mapping.get(score, 'D')  # Default to D if unknown
        
        # Convert checkbox values to letter grades and create trait score dictionary
        all_scores = page2_values + page3_values + page4_values
        trait_scores = {}
        for i, score in enumerate(all_scores):
            if i < len(TRAIT_NAMES):
                trait_scores[TRAIT_NAMES[i]] = score_to_letter(score)
        
        # Use proper FRA calculation that handles H grades correctly
        fra_score = calculate_fra_score(trait_scores)

        # Check if this is a non-observed report (FRA score is None when all traits are H)
        if fra_score is None:
            print(f"  ⚠️  Skipping non-observed report (all traits marked H)")
            return "non_observed"

        fitrep_data["fra_score"] = float(fra_score)

        # Create FitReport
        db_fitrep = FitReport(**fitrep_data)
        db.add(db_fitrep)
        db.commit()
        db.refresh(db_fitrep)
        
        # Create trait scores
        trait_names = [
            "Mission Accomplishment", "Proficiency", "Individual Character", 
            "Effectiveness Under Stress", "Initiative", "Leadership",
            "Developing Subordinates", "Setting the Example", 
            "Ensuring Well-being of Subordinates", "Communication Skills",
            "Intellect and Wisdom", "Decision Making Ability", "Judgment", 
            "Fulfillment of Evaluation Responsibilities"
        ]
        
        def score_to_letter(score):
            mapping = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F', 7: 'G', 8: 'H'}
            return mapping.get(score, 'D')
        
        for i, trait_name in enumerate(trait_names):
            if i < len(all_scores):
                trait_score = TraitScore(
                    fitrep_id=db_fitrep.id,
                    trait_name=trait_name,
                    trait_order=i + 1,
                    score_letter=score_to_letter(all_scores[i]),
                    score_numeric=all_scores[i]
                )
                db.add(trait_score)
        
        db.commit()
        return "success"
        
    except Exception as e:
        print(f"Error processing single FITREP: {str(e)}")
        return False

@router.post("/smart-upload")
async def smart_upload_with_officer_info(
    files: List[UploadFile] = File(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    service_number: str = Form(...),
    current_rank: str = Form(...),
    middle_initial: str = Form(""),
    db: Session = Depends(get_db)
):
    """
    Smart upload: Create officer profile from basic info and process FITREP files.
    This takes minimal officer info and extracts everything else from the reports.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    try:
        # Create officer data
        officer_data = {
            "last_name": last_name.upper(),
            "first_name": first_name.upper(), 
            "middle_initial": middle_initial.upper() if middle_initial else None,
            "service_number": service_number,
            "current_rank": current_rank.upper()
        }
        
        # Check if officer already exists by service number
        existing_officer = db.query(Officer).filter(Officer.service_number == service_number).first()
        if existing_officer:
            # Update existing officer info
            for key, value in officer_data.items():
                if value:  # Only update non-empty values
                    setattr(existing_officer, key, value)
            db.commit()
            officer_id = existing_officer.id
        else:
            # Create new officer
            db_officer = Officer(**officer_data)
            db.add(db_officer)
            db.commit()
            db.refresh(db_officer)
            officer_id = db_officer.id
        
        # Process all files with the officer_id
        # Note: We'll use a simplified processor that works with our local extractor
        return await process_fitrep_files_local(files, officer_id, db)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in smart upload: {str(e)}")

async def process_fitrep_files_local(
    files: List[UploadFile],
    officer_id: int, 
    db: Session
):
    """
    Process FITREP files using local extractor instead of external service.
    """
    officer = db.query(Officer).filter(Officer.id == officer_id).first()
    if not officer:
        raise HTTPException(status_code=404, detail="Officer not found")
    
    results = []
    
    # Process each file with our local extractor
    for i, file in enumerate(files):
        try:
            import tempfile
            import shutil
            from pathlib import Path
            import sys
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                shutil.copyfileobj(file.file, tmp_file)
                tmp_file_path = tmp_file.name
            
            # Extract data using local extractor
            # Get the absolute path to the project root
            project_root = Path(__file__).parent.parent.parent.parent.absolute()
            extractor_path = project_root / "fitrep_extractor.py"
            
            # Import using absolute path
            import importlib.util
            if extractor_path.exists():
                spec = importlib.util.spec_from_file_location("fitrep_extractor", str(extractor_path))
                fitrep_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(fitrep_module)
                FITREPExtractor = fitrep_module.FITREPExtractor
            else:
                raise ImportError(f"Cannot find fitrep_extractor.py at {extractor_path}")
            
            extractor = FITREPExtractor()
            extracted_data = extractor.extract_from_pdf(Path(tmp_file_path))
            
            # Clean up temp file
            os.unlink(tmp_file_path)
            
            # Debug: Show RS data from each individual FITREP
            if extracted_data:
                rs_from_this_file = {
                    'rs_first_name': extracted_data.get('rs_first_name'),
                    'rs_last_name': extracted_data.get('rs_last_name'), 
                    'rs_edipi': extracted_data.get('rs_edipi'),
                    'marine_name': extracted_data.get('last_name')
                }
                print(f"    File {i+1} ({file.filename}): RS={rs_from_this_file}")
            
            if not extracted_data:
                results.append({
                    "filename": file.filename,
                    "status": "error", 
                    "error": "Could not extract data from PDF"
                })
                continue
            
            # Convert extracted data to the format expected by the database
            admin_info = {
                "fitrep_id": f"AUTO_{officer_id}_{len(results)}",
                "rank": extracted_data.get('grade', 'UNKNOWN'),
                "period_to": extracted_data.get('to_date', ''),
                "occasion_type": "AN"
            }
            
            # Create mock trait scores (since extractor gives checkbox values)
            trait_scores = {}
            trait_names = [
                "Mission Accomplishment", "Proficiency", "Individual Character",
                "Effectiveness Under Stress", "Initiative", "Leadership", 
                "Developing Subordinates", "Setting the Example",
                "Ensuring Well-being of Subordinates", "Communication Skills",
                "Intellect and Wisdom", "Decision Making Ability", "Judgment",
                "Fulfillment of Evaluation Responsibilities"
            ]
            
            # Convert numeric scores to letter grades
            def score_to_letter(score):
                if score == 1: return 'A'
                elif score == 2: return 'B' 
                elif score == 3: return 'C'
                elif score == 4: return 'D'
                elif score == 5: return 'E'
                else: return 'D'
            
            # Use extracted checkbox values
            page2_values = extracted_data.get('page2_values', [4] * 5)
            page3_values = extracted_data.get('page3_values', [4] * 5) 
            page4_values = extracted_data.get('page4_values', [4] * 4)
            all_values = page2_values + page3_values + page4_values
            
            for i, trait_name in enumerate(trait_names):
                if i < len(all_values):
                    trait_scores[trait_name] = score_to_letter(all_values[i])
                else:
                    trait_scores[trait_name] = 'D'  # Default
            
            rs_info = {
                "name": f"{officer.last_name}, {officer.first_name}",
                "rank": officer.current_rank
            }
            
            formatted_data = {
                "administrative_info": admin_info,
                "trait_scores": trait_scores, 
                "reporting_senior_info": rs_info
            }
            
            # Save to database
            fitrep_record = await _save_fitrep_data(formatted_data, officer_id, db)
            
            results.append({
                "filename": file.filename,
                "status": "success",
                "fitrep_id": fitrep_record.fitrep_id,
                "fra_score": float(fitrep_record.fra_score) if fitrep_record.fra_score else None
            })
            
        except Exception as e:
            import traceback
            error_details = f"{str(e)} | Traceback: {traceback.format_exc()}"
            results.append({
                "filename": file.filename,
                "status": "error", 
                "error": error_details
            })
            print(f"ERROR processing {file.filename}: {error_details}")
    
    # Recalculate relative values
    await _recalculate_relative_values(officer_id, db)
    
    return {
        "total_files": len(files),
        "successful": len([r for r in results if r["status"] == "success"]),
        "failed": len([r for r in results if r["status"] == "error"]),
        "results": results,
        "officer_id": officer_id
    }

@router.post("/process-files")
async def process_fitrep_files(
    files: List[UploadFile] = File(...),
    officer_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    Process uploaded FITREP PDF files for existing officer.
    """
    return await process_fitrep_files_internal(files, officer_id, db)

async def process_fitrep_files_internal(
    files: List[UploadFile],
    officer_id: int,
    db: Session
):
    """
    Process uploaded FITREP PDF files and extract data.
    """
    # Verify officer exists
    officer = db.query(Officer).filter(Officer.id == officer_id).first()
    if not officer:
        raise HTTPException(status_code=404, detail="Officer not found")
    
    results = []
    
    # Process each file with the PDF processor service
    for file in files:
        try:
            # Send file to PDF processor
            pdf_processor_url = os.getenv("PDF_PROCESSOR_URL", "http://pdf-processor:8001")
            
            async with httpx.AsyncClient() as client:
                files_payload = {"file": (file.filename, await file.read(), file.content_type)}
                response = await client.post(f"{pdf_processor_url}/extract-fitrep", files=files_payload)
            
            if response.status_code != 200:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": f"PDF processing failed: {response.text}"
                })
                continue
            
            extracted_data = response.json()["data"]
            
            # Process extracted data and save to database
            fitrep_record = await _save_fitrep_data(extracted_data, officer_id, db)
            
            results.append({
                "filename": file.filename,
                "status": "success",
                "fitrep_id": fitrep_record.fitrep_id,
                "fra_score": float(fitrep_record.fra_score) if fitrep_record.fra_score else None
            })
            
        except Exception as e:
            import traceback
            error_details = f"{str(e)} | Traceback: {traceback.format_exc()}"
            results.append({
                "filename": file.filename,
                "status": "error", 
                "error": error_details
            })
            print(f"ERROR processing {file.filename}: {error_details}")
    
    # Recalculate relative values for all reports from same reporting seniors
    await _recalculate_relative_values(officer_id, db)
    
    return {
        "total_files": len(files),
        "successful": len([r for r in results if r["status"] == "success"]),
        "failed": len([r for r in results if r["status"] == "error"]),
        "results": results
    }

async def _save_fitrep_data(extracted_data: Dict, officer_id: int, db: Session) -> FitReport:
    """Save extracted FITREP data to database."""
    
    admin_info = extracted_data.get("administrative_info", {})
    trait_scores = extracted_data.get("trait_scores", {})
    rs_info = extracted_data.get("reporting_senior_info", {})
    
    # Helper function to convert empty strings to None for date fields
    def parse_date_or_none(date_str):
        if not date_str or date_str.strip() == "":
            return None
        try:
            from datetime import datetime
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None
    
    # Parse key fields for duplicate checking
    fitrep_id = admin_info.get("fitrep_id") or f"UNKNOWN_{officer_id}_{len(extracted_data.get('trait_scores', {}))}"
    period_to = parse_date_or_none(admin_info.get("period_to"))
    
    # Check for duplicates by FITREP ID or end date for the same officer
    if fitrep_id != f"UNKNOWN_{officer_id}_{len(extracted_data.get('trait_scores', {}))}":
        # Check by FITREP ID
        existing_by_id = db.query(FitReport).filter(
            FitReport.officer_id == officer_id,
            FitReport.fitrep_id == fitrep_id
        ).first()
        
        if existing_by_id:
            raise ValueError(f"Duplicate FITREP detected: FITREP ID '{fitrep_id}' already exists for this officer")
    
    if period_to:
        # Check by end date
        existing_by_date = db.query(FitReport).filter(
            FitReport.officer_id == officer_id,
            FitReport.period_to == period_to
        ).first()
        
        if existing_by_date:
            raise ValueError(f"Duplicate FITREP detected: A report with end date '{period_to}' already exists for this officer")
    
    # Create FitReport record
    fitrep = FitReport(
        officer_id=officer_id,
        fitrep_id=fitrep_id,
        report_date=parse_date_or_none(admin_info.get("report_date")),
        period_from=parse_date_or_none(admin_info.get("period_from")),
        period_to=parse_date_or_none(admin_info.get("period_to")),
        rank_at_time=admin_info.get("rank") or "UNKNOWN",
        organization=admin_info.get("organization"),
        reporting_senior_name=rs_info.get("name"),
        reporting_senior_rank=rs_info.get("rank"),
        occasion_type=admin_info.get("occasion_type", "AN")
    )
    
    # Calculate FRA score from trait scores
    if trait_scores:
        fra_score = calculate_fra_score(trait_scores)
        fitrep.fra_score = fra_score
    
    db.add(fitrep)
    db.commit()
    db.refresh(fitrep)
    
    # Save individual trait scores
    for i, (trait_name, letter_grade) in enumerate(trait_scores.items(), 1):
        trait_score = TraitScore(
            fitrep_id=fitrep.id,
            trait_name=trait_name,
            trait_order=i,
            score_letter=letter_grade,
            score_numeric=None if letter_grade == 'H' else ord(letter_grade) - ord('A') + 1
        )
        db.add(trait_score)
    
    db.commit()
    
    return fitrep

async def _recalculate_relative_values(officer_id: int, db: Session):
    """Recalculate relative values for all FITREPs from the same reporting seniors."""
    
    # Get all FITREPs for this officer
    fitreports = db.query(FitReport).filter(FitReport.officer_id == officer_id).all()
    
    # Group by rank and reporting senior
    groups = {}
    for report in fitreports:
        if not report.fra_score or not report.reporting_senior_name:
            continue
            
        # Exclude EN (End of Active Service) reports from RV calculations
        if report.occasion_type and report.occasion_type.upper() == 'EN':
            continue
            
        key = (report.rank_at_time, report.reporting_senior_name)
        if key not in groups:
            groups[key] = []
        groups[key].append((report.id, report.fra_score))
    
    # Calculate RV for each group
    for (rank, rs_name), fra_scores in groups.items():
        if len(fra_scores) >= 3:  # Need at least 3 reports for RV calculation
            rv_results = calculate_relative_values(fra_scores, rank, rs_name)
            
            # Save/update RV records
            for fitrep_id, rv_data in rv_results.items():
                # Delete existing RV record
                db.query(RelativeValue).filter(RelativeValue.fitrep_id == fitrep_id).delete()
                
                # Create new RV record
                rv_record = RelativeValue(
                    fitrep_id=fitrep_id,
                    rank=rv_data["rank"],
                    reporting_senior=rv_data["reporting_senior"],
                    relative_value=rv_data["relative_value"],
                    total_reports_for_rank=rv_data["total_reports_for_rank"],
                    highest_fra_for_rank=rv_data["highest_fra_for_rank"],
                    average_fra_for_rank=rv_data["average_fra_for_rank"],
                    minimum_fra_for_rank=rv_data["minimum_fra_for_rank"]
                )
                db.add(rv_record)
    
    db.commit()

async def _recalculate_all_relative_values(db: Session):
    """Recalculate relative values for all FITREPs across all reporting seniors."""
    
    print("  Analyzing all FITREPs for RV calculation...")
    
    # Get all FITREPs and group by rank and reporting senior
    all_reports = db.query(FitReport).filter(
        FitReport.fra_score.is_not(None),
        FitReport.reporting_senior_name.is_not(None)
    ).all()
    
    # Group by (rank, reporting_senior)
    groups = {}
    for report in all_reports:
        # Exclude EN (End of Active Service) reports from RV calculations
        if report.occasion_type and report.occasion_type.upper() == 'EN':
            continue
            
        key = (report.rank_at_time, report.reporting_senior_name)
        if key not in groups:
            groups[key] = []
        groups[key].append((report.id, report.fra_score))
    
    total_groups = len(groups)
    groups_with_rv = 0
    
    # Calculate RV for each group that has enough reports
    for (rank, rs_name), fra_scores in groups.items():
        if len(fra_scores) >= 3:  # Need at least 3 reports for RV calculation
            print(f"  Calculating RV for {rs_name} {rank} rank ({len(fra_scores)} reports)")
            
            rv_results = calculate_relative_values(fra_scores, rank, rs_name)
            
            # Save/update RV records
            for fitrep_id, rv_data in rv_results.items():
                # Delete existing RV record
                db.query(RelativeValue).filter(RelativeValue.fitrep_id == fitrep_id).delete()
                
                # Create new RV record
                rv_record = RelativeValue(
                    fitrep_id=fitrep_id,
                    rank=rv_data["rank"],
                    reporting_senior=rv_data["reporting_senior"],
                    relative_value=rv_data["relative_value"],
                    total_reports_for_rank=rv_data["total_reports_for_rank"],
                    highest_fra_for_rank=rv_data["highest_fra_for_rank"],
                    average_fra_for_rank=rv_data["average_fra_for_rank"],
                    minimum_fra_for_rank=rv_data["minimum_fra_for_rank"]
                )
                db.add(rv_record)
            
            groups_with_rv += 1
        else:
            print(f"  Skipping {rs_name} {rank} rank (only {len(fra_scores)} reports, need 3+)")
    
    print(f"  Calculated RV values for {groups_with_rv}/{total_groups} rank/RS combinations")
    db.commit()

@router.post("/recalculate-all-rv")
async def recalculate_all_rv(db: Session = Depends(get_db)):
    """Manually trigger recalculation of all relative values."""
    try:
        await _recalculate_all_relative_values(db)
        return {"message": "Successfully recalculated all relative values"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recalculating RV values: {str(e)}")

@router.post("/import-rs-list")
async def import_rs_list(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import FITREPs from a Reporting Senior's List PDF.

    This creates a complete profile from the standardized RS list format,
    generating synthetic trait scores that match the documented FRA values.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_file_path = tmp_file.name

        # Parse the RS list PDF
        rs_data = parse_rs_list_pdf(tmp_file_path)

        # Clean up temp file
        os.unlink(tmp_file_path)

        # Create or get Reporting Senior officer record
        rs_name = rs_data['rs_name']
        rs_rank = rs_data['rs_rank']
        rs_dod_id = rs_data['rs_dod_id']

        # Parse name (e.g., "JANE A SMITH" -> first: JANE, middle: A, last: SMITH)
        name_parts = rs_name.strip().split()

        if len(name_parts) >= 3:
            first_name = name_parts[0]
            middle_initial = name_parts[1][0] if len(name_parts[1]) == 1 else None
            last_name = ' '.join(name_parts[2:] if middle_initial else name_parts[1:])
        elif len(name_parts) == 2:
            first_name = name_parts[0]
            last_name = name_parts[1]
            middle_initial = None
        else:
            first_name = "UNKNOWN"
            last_name = rs_name
            middle_initial = None

        # Check if RS already exists
        existing_rs = None
        if rs_dod_id:
            existing_rs = db.query(Officer).filter(Officer.service_number == rs_dod_id).first()

        if existing_rs:
            officer_id = existing_rs.id
            # Update names from parsed data in case they differ
            first_name = existing_rs.first_name
            last_name = existing_rs.last_name
            print(f"Found existing RS: {existing_rs.last_name} (ID: {officer_id})")
        else:
            # Create new RS officer
            rs_officer = Officer(
                service_number=rs_dod_id or f"AUTO_{int(datetime.now().timestamp())}",
                first_name=first_name,
                middle_initial=middle_initial,
                last_name=last_name,
                current_rank=rs_rank
            )
            db.add(rs_officer)
            db.commit()
            db.refresh(rs_officer)
            officer_id = rs_officer.id
            print(f"Created new RS: {last_name} (ID: {officer_id})")

        # Process each FITREP from the list
        imported_count = 0
        skipped_count = 0
        skipped_reasons = []

        for fitrep_data in rs_data['fitreports']:
            try:
                # Skip if no FRA score (N/A or missing)
                if not fitrep_data['fra']:
                    skipped_count += 1
                    skipped_reasons.append(f"{fitrep_data['last_name']} ({fitrep_data['from_date']} to {fitrep_data['to_date']}): No FRA score")
                    continue

                # Skip EN occasion reports
                if fitrep_data['occasion'] and fitrep_data['occasion'].upper() == 'EN':
                    skipped_count += 1
                    skipped_reasons.append(f"{fitrep_data['last_name']} ({fitrep_data['from_date']} to {fitrep_data['to_date']}): EN report (excluded from RV)")
                    continue

                # Generate dummy FITREP ID
                fitrep_id = generate_dummy_fitrep_id(
                    fitrep_data['edipi'],
                    fitrep_data['from_date'],
                    fitrep_data['to_date']
                )

                # Check for duplicates
                existing_fitrep = db.query(FitReport).filter(
                    FitReport.officer_id == officer_id,
                    FitReport.fitrep_id == str(fitrep_id)
                ).first()

                if existing_fitrep:
                    skipped_count += 1
                    skipped_reasons.append(f"{fitrep_data['last_name']} ({fitrep_data['from_date']} to {fitrep_data['to_date']}): Duplicate")
                    continue

                # Generate synthetic trait scores that match the FRA
                trait_scores = generate_trait_scores_from_fra(fitrep_data['fra'])

                # Create FITREP record
                fitrep = FitReport(
                    officer_id=officer_id,
                    fitrep_id=str(fitrep_id),
                    period_from=datetime.strptime(fitrep_data['from_date'], '%Y-%m-%d').date(),
                    period_to=datetime.strptime(fitrep_data['to_date'], '%Y-%m-%d').date(),
                    report_date=datetime.strptime(fitrep_data['to_date'], '%Y-%m-%d').date(),
                    rank_at_time=fitrep_data['grade'],
                    occasion_type=fitrep_data['occasion'] or 'AN',
                    fra_score=float(fitrep_data['fra']),
                    reporting_senior_name=f"{last_name}, {first_name}",
                    organization=f"Marine: {fitrep_data['last_name']} (EDIPI: {fitrep_data['edipi']})"
                )

                db.add(fitrep)
                db.commit()
                db.refresh(fitrep)

                # Save trait scores
                for i, (trait_name, letter_grade) in enumerate(trait_scores.items(), 1):
                    trait_score = TraitScore(
                        fitrep_id=fitrep.id,
                        trait_name=trait_name,
                        trait_order=i,
                        score_letter=letter_grade,
                        score_numeric=None if letter_grade == 'H' else ord(letter_grade) - ord('A') + 1
                    )
                    db.add(trait_score)

                db.commit()
                imported_count += 1

            except Exception as e:
                skipped_count += 1
                skipped_reasons.append(f"{fitrep_data['last_name']} ({fitrep_data['from_date']} to {fitrep_data['to_date']}): Error - {str(e)}")
                continue

        # Recalculate relative values
        await _recalculate_relative_values(officer_id, db)

        return {
            "message": f"Successfully imported {imported_count} FITREPs for {last_name}",
            "officer_id": officer_id,
            "officer_name": f"{last_name}, {first_name}",
            "total_in_list": len(rs_data['fitreports']),
            "imported": imported_count,
            "skipped": skipped_count,
            "skipped_reasons": skipped_reasons[:10]  # Limit to first 10 for display
        }

    except Exception as e:
        import traceback
        error_details = f"{str(e)} | Traceback: {traceback.format_exc()}"
        print(f"RS LIST IMPORT ERROR: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error importing RS list: {str(e)}")

@router.delete("/all")
async def delete_all_fitreports(db: Session = Depends(get_db)):
    """Delete ALL FITREPs across all officers."""
    # Delete related records first to avoid foreign key constraint violations
    db.query(RelativeValue).delete()
    db.query(TraitScore).delete()

    # Delete all FITREPs
    deleted_count = db.query(FitReport).delete()
    db.commit()

    return {"message": f"Deleted all {deleted_count} FITREPs from database"}

@router.delete("/officer/{officer_id}/all")
async def delete_all_officer_fitreports(officer_id: int, db: Session = Depends(get_db)):
    """Delete all FITREPs for a specific officer."""
    officer = db.query(Officer).filter(Officer.id == officer_id).first()
    if not officer:
        raise HTTPException(status_code=404, detail="Officer not found")

    # Get all FITREP IDs for this officer
    fitrep_ids = [f.id for f in db.query(FitReport).filter(FitReport.officer_id == officer_id).all()]

    # Delete related records first to avoid foreign key constraint violations
    db.query(RelativeValue).filter(RelativeValue.fitrep_id.in_(fitrep_ids)).delete(synchronize_session=False)
    db.query(TraitScore).filter(TraitScore.fitrep_id.in_(fitrep_ids)).delete(synchronize_session=False)

    # Delete all FITREPs for this officer
    deleted_count = db.query(FitReport).filter(FitReport.officer_id == officer_id).delete()
    db.commit()

    return {"message": f"Deleted {deleted_count} FITREPs for officer {officer_id}"}

@router.delete("/{fitrep_id}")
async def delete_fitrep(fitrep_id: int, db: Session = Depends(get_db)):
    """Delete a specific FITREP and all associated data."""
    fitrep = db.query(FitReport).filter(FitReport.id == fitrep_id).first()
    if not fitrep:
        raise HTTPException(status_code=404, detail="FITREP not found")

    # Delete related records first to avoid foreign key constraint violations
    db.query(RelativeValue).filter(RelativeValue.fitrep_id == fitrep_id).delete()
    db.query(TraitScore).filter(TraitScore.fitrep_id == fitrep_id).delete()

    # Delete the FITREP
    db.delete(fitrep)
    db.commit()

    return {"message": "FITREP deleted successfully"}