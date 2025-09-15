from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.database import get_db
from app.models.models import Officer, FitReport, RelativeValue, TraitScore
from typing import Dict, List, Optional
from pydantic import BaseModel

router = APIRouter()

class RankProfileData(BaseModel):
    total_reports: int
    average_fra: float
    highest_fra: float
    lowest_fra: float
    average_rv: Optional[float]
    reports: List[Dict]

class TraitScoreResponse(BaseModel):
    trait_name: str
    score_letter: str

class FitReportDetail(BaseModel):
    fitrep_id: str
    rank_at_time: str
    period_from: str
    period_to: str
    fra_score: Optional[float]
    relative_value: Optional[int]
    organization: Optional[str]
    reporting_senior_name: Optional[str]
    trait_scores: List[TraitScoreResponse]

class Marine(BaseModel):
    last_name: str
    first_name: str
    fitreports: List[FitReportDetail]

class ProfileResponse(BaseModel):
    officer_info: Dict
    rank_breakdown: Dict[str, RankProfileData]
    marines: List[Marine]

@router.get("/{officer_id}", response_model=ProfileResponse)
async def get_officer_profile(officer_id: int, db: Session = Depends(get_db)):
    """Get comprehensive profile data for a Reporting Senior officer."""
    
    # Get the reporting senior officer
    reporting_senior = db.query(Officer).filter(Officer.id == officer_id).first()
    if not reporting_senior:
        raise HTTPException(status_code=404, detail="Officer not found")
    
    # Get all FITREPs where this officer is the reporting senior
    rs_fitreports = db.query(FitReport).filter(
        FitReport.reporting_senior_name == f"{reporting_senior.last_name}, {reporting_senior.first_name}"
    ).all()
    
    if not rs_fitreports:
        raise HTTPException(status_code=404, detail="No FITREPs found where this officer is the Reporting Senior")
    
    # Group by rank for the rank breakdown (only reports written by this RS)
    rank_data = {}
    
    # Group by Marine for the marines list (only Marines reported on by this RS)
    marines_data = {}
    
    for report in rs_fitreports:
        officer = report.officer
        marine_key = f"{officer.last_name}, {officer.first_name}"
        
        # Get relative value for this report
        rv_record = db.query(RelativeValue).filter(RelativeValue.fitrep_id == report.id).first()
        relative_value = rv_record.relative_value if rv_record else None
        
        # Get trait scores for this report
        trait_scores_records = db.query(TraitScore).filter(TraitScore.fitrep_id == report.id).order_by(TraitScore.trait_order).all()
        trait_scores = {}
        trait_scores_list = []
        for trait in trait_scores_records:
            trait_scores[trait.trait_name] = trait.score_letter or 'D'
            trait_scores_list.append(TraitScoreResponse(
                trait_name=trait.trait_name,
                score_letter=trait.score_letter or 'D'
            ))
        
        # Add to rank breakdown (reports by this RS for this rank only)
        rank = report.rank_at_time
        if rank not in rank_data:
            rank_data[rank] = []
        
        rank_data[rank].append({
            "fitrep_id": report.fitrep_id,
            "period": f"{report.period_from} to {report.period_to}",
            "fra_score": float(report.fra_score) if report.fra_score else 0.0,
            "relative_value": relative_value,
            "reporting_senior": report.reporting_senior_name or "Unknown",
            "organization": report.organization or "Unknown",
            "trait_scores": trait_scores,
            "marine_name": marine_key
        })
        
        # Add to marines data (only Marines reported on by this RS)
        if marine_key not in marines_data:
            marines_data[marine_key] = {
                "last_name": officer.last_name,
                "first_name": officer.first_name,
                "fitreports": []
            }
        
        marines_data[marine_key]["fitreports"].append(FitReportDetail(
            fitrep_id=report.fitrep_id,
            rank_at_time=report.rank_at_time,
            period_from=str(report.period_from),
            period_to=str(report.period_to),
            fra_score=float(report.fra_score) if report.fra_score else None,
            relative_value=relative_value,
            organization=report.organization,
            reporting_senior_name=report.reporting_senior_name,
            trait_scores=trait_scores_list
        ))
    
    # Calculate statistics for each rank (only for reports by this RS, excluding EN reports from averages)
    rank_breakdown = {}
    for rank, reports in rank_data.items():
        # Separate EN reports from regular reports for statistics
        regular_reports = []
        all_reports = []
        
        for report in reports:
            all_reports.append(report)
            # Find the original FitReport to check occasion_type
            fitrep_record = None
            for fr in rs_fitreports:
                if fr.fitrep_id == report["fitrep_id"]:
                    fitrep_record = fr
                    break
            
            # Include in statistics only if not EN report
            if not fitrep_record or not fitrep_record.occasion_type or fitrep_record.occasion_type.upper() != 'EN':
                regular_reports.append(report)
        
        # Calculate statistics based on regular reports only
        fra_scores = [r["fra_score"] for r in regular_reports if r["fra_score"] > 0]
        rv_values = [r["relative_value"] for r in regular_reports if r["relative_value"] is not None]
        
        if fra_scores:
            rank_breakdown[rank] = RankProfileData(
                total_reports=len(all_reports),  # Show all reports in count
                average_fra=sum(fra_scores) / len(fra_scores),  # But average excludes EN
                highest_fra=max(fra_scores),
                lowest_fra=min(fra_scores),
                average_rv=sum(rv_values) / len(rv_values) if rv_values else None,
                reports=all_reports  # Show all reports including EN
            )
    
    # Convert marines data to list (only Marines reported on by this RS)
    marines_list = [Marine(**marine_data) for marine_data in marines_data.values()]
    
    # Sort marines by last name
    marines_list.sort(key=lambda m: m.last_name)
    
    officer_info = {
        "name": f"{reporting_senior.last_name}, {reporting_senior.first_name} {reporting_senior.middle_initial or ''}".strip(),
        "rank": reporting_senior.current_rank,
        "total_reports": len(rs_fitreports)
    }
    
    return ProfileResponse(
        officer_info=officer_info,
        rank_breakdown=rank_breakdown,
        marines=marines_list
    )

@router.get("/{officer_id}/summary")
async def get_profile_summary(officer_id: int, db: Session = Depends(get_db)):
    """Get quick summary of officer profile."""
    
    officer = db.query(Officer).filter(Officer.id == officer_id).first()
    if not officer:
        raise HTTPException(status_code=404, detail="Officer not found")
    
    # Get latest FITREP
    latest_fitrep = db.query(FitReport).filter(FitReport.officer_id == officer_id).order_by(FitReport.report_date.desc()).first()
    
    total_reports = db.query(FitReport).filter(FitReport.officer_id == officer_id).count()
    
    latest_rv = None
    if latest_fitrep:
        rv_record = db.query(RelativeValue).filter(RelativeValue.fitrep_id == latest_fitrep.id).first()
        latest_rv = rv_record.relative_value if rv_record else None
    
    return {
        "officer_name": f"{officer.last_name}, {officer.first_name} {officer.middle_initial or ''}".strip(),
        "current_rank": officer.current_rank,
        "total_reports": total_reports,
        "latest_fra": float(latest_fitrep.fra_score) if latest_fitrep and latest_fitrep.fra_score else 0.0,
        "latest_rv": latest_rv or 0
    }

@router.get("/")
async def list_reporting_seniors(db: Session = Depends(get_db)):
    """List all officers who have served as Reporting Seniors."""
    
    # Find all unique reporting seniors who have written FITREPs
    rs_names = db.query(FitReport.reporting_senior_name).distinct().filter(
        FitReport.reporting_senior_name.is_not(None)
    ).all()
    
    reporting_seniors = []
    for rs_name_tuple in rs_names:
        rs_name = rs_name_tuple[0]
        if not rs_name:
            continue
            
        # Try to find the officer by name
        # Parse name format "LAST, FIRST" or "LAST, FIRST MIDDLE"
        name_parts = rs_name.split(', ')
        if len(name_parts) == 2:
            last_name = name_parts[0].strip()
            first_part = name_parts[1].strip().split()
            first_name = first_part[0] if first_part else ""
            
            officer = db.query(Officer).filter(
                Officer.last_name == last_name,
                Officer.first_name == first_name
            ).first()
            
            if officer:
                # Count reports written by this RS
                reports_count = db.query(FitReport).filter(
                    FitReport.reporting_senior_name == rs_name
                ).count()
                
                reporting_seniors.append({
                    "id": officer.id,
                    "name": rs_name,
                    "rank": officer.current_rank,
                    "reports_written": reports_count
                })
    
    return {
        "reporting_seniors": reporting_seniors,
        "count": len(reporting_seniors)
    }