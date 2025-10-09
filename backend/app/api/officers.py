from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.models import Officer, FitReport, Profile
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()

class OfficerCreate(BaseModel):
    last_name: str
    first_name: str
    middle_initial: Optional[str] = None
    service_number: str
    current_rank: str

class OfficerResponse(BaseModel):
    id: int
    last_name: str
    first_name: str
    middle_initial: Optional[str]
    service_number: str
    current_rank: str
    total_reports: int

    class Config:
        from_attributes = True

@router.get("/", response_model=List[OfficerResponse])
async def get_officers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get list of all officers with at least one FITREP."""
    officers = db.query(Officer).offset(skip).limit(limit).all()

    # Add total reports count and filter out officers with 0 reports
    officer_responses = []
    for officer in officers:
        total_reports = db.query(FitReport).filter(FitReport.officer_id == officer.id).count()

        # Only include officers with at least one report
        if total_reports > 0:
            officer_data = OfficerResponse(
                id=officer.id,
                last_name=officer.last_name,
                first_name=officer.first_name,
                middle_initial=officer.middle_initial,
                service_number=officer.service_number,
                current_rank=officer.current_rank,
                total_reports=total_reports
            )
            officer_responses.append(officer_data)

    return officer_responses

@router.get("/{officer_id}", response_model=OfficerResponse)
async def get_officer(officer_id: int, db: Session = Depends(get_db)):
    """Get specific officer by ID."""
    officer = db.query(Officer).filter(Officer.id == officer_id).first()
    if not officer:
        raise HTTPException(status_code=404, detail="Officer not found")
    
    total_reports = db.query(FitReport).filter(FitReport.officer_id == officer.id).count()
    
    return OfficerResponse(
        id=officer.id,
        last_name=officer.last_name,
        first_name=officer.first_name,
        middle_initial=officer.middle_initial,
        service_number=officer.service_number,
        current_rank=officer.current_rank,
        total_reports=total_reports
    )

@router.post("/", response_model=OfficerResponse)
async def create_officer(officer: OfficerCreate, db: Session = Depends(get_db)):
    """Create a new officer."""
    # Check if officer already exists by service number
    existing_officer = db.query(Officer).filter(Officer.service_number == officer.service_number).first()
    if existing_officer:
        raise HTTPException(status_code=400, detail="Officer with this service number already exists")
    
    db_officer = Officer(**officer.dict())
    db.add(db_officer)
    db.commit()
    db.refresh(db_officer)
    
    return OfficerResponse(
        id=db_officer.id,
        last_name=db_officer.last_name,
        first_name=db_officer.first_name,
        middle_initial=db_officer.middle_initial,
        service_number=db_officer.service_number,
        current_rank=db_officer.current_rank,
        total_reports=0
    )