from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.models import Officer, FitReport, RelativeValue
from app.utils.scoring import predict_impact, validate_trait_scores, calculate_fra_score
from typing import List, Dict
from pydantic import BaseModel
from decimal import Decimal

router = APIRouter()

class PredictImpactRequest(BaseModel):
    officer_id: int
    rank: str
    reporting_senior: str
    proposed_reports: List[Dict[str, str]]  # List of trait scores for new reports

class PredictImpactResponse(BaseModel):
    current: Dict
    predicted: Dict
    updated_existing_reports: List[Dict]
    new_reports: List[Dict]

class ValidateScoresRequest(BaseModel):
    trait_scores: Dict[str, str]

@router.post("/predict-impact", response_model=PredictImpactResponse)
async def predict_report_impact(
    request: PredictImpactRequest,
    db: Session = Depends(get_db)
):
    """
    Predict the impact of adding new FITREP reports to a Reporting Senior's profile.
    This calculates how new reports would affect the RS's averages and RV calculations.
    """
    
    # Verify reporting senior exists
    officer = db.query(Officer).filter(Officer.id == request.officer_id).first()
    if not officer:
        raise HTTPException(status_code=404, detail="Reporting Senior not found")
    
    # Get current FRA scores for all Marines this RS has reported on for the specified rank
    # Exclude EN (End of Active Service) reports from impact calculations
    print(f"DEBUG: Searching for RS='{request.reporting_senior}', rank='{request.rank}'")
    
    current_reports = db.query(FitReport).filter(
        FitReport.reporting_senior_name == request.reporting_senior,
        FitReport.rank_at_time == request.rank,
        FitReport.fra_score.is_not(None),
        FitReport.occasion_type != 'EN'
    ).all()
    
    print(f"DEBUG: Found {len(current_reports)} current reports")
    for report in current_reports:
        print(f"DEBUG: Report {report.fitrep_id}: FRA={report.fra_score}, RS='{report.reporting_senior_name}'")
    
    current_fra_scores = [Decimal(str(report.fra_score)) for report in current_reports]
    current_report_ids = [report.fitrep_id for report in current_reports]
    
    print(f"DEBUG: FRA scores: {current_fra_scores}")
    print(f"DEBUG: Report IDs: {current_report_ids}")
    
    # Calculate FRA scores for proposed reports
    new_fra_scores = []
    for trait_scores in request.proposed_reports:
        # Validate trait scores
        validation_errors = validate_trait_scores(trait_scores)
        if validation_errors:
            raise HTTPException(status_code=400, detail=f"Invalid trait scores: {'; '.join(validation_errors)}")
        
        fra_score = calculate_fra_score(trait_scores)
        if fra_score is None:
            raise HTTPException(status_code=400, detail="Could not calculate FRA score from provided trait scores")
        
        new_fra_scores.append(fra_score)
    
    # Predict impact
    impact_analysis = predict_impact(
        current_fra_scores=current_fra_scores,
        new_fra_scores=new_fra_scores,
        rank=request.rank,
        reporting_senior=request.reporting_senior,
        current_report_ids=current_report_ids
    )
    
    print(f"DEBUG: Impact analysis result:")
    print(f"DEBUG: Current: {impact_analysis['current']}")
    print(f"DEBUG: Predicted: {impact_analysis['predicted']}")
    print(f"DEBUG: Updated existing: {impact_analysis['updated_existing_reports']}")
    print(f"DEBUG: New reports: {impact_analysis['new_reports']}")
    
    return PredictImpactResponse(**impact_analysis)

@router.post("/validate-trait-scores")
async def validate_trait_scores_endpoint(request: ValidateScoresRequest):
    """
    Validate a set of trait scores for completeness and correctness.
    """
    
    validation_errors = validate_trait_scores(request.trait_scores)
    
    if validation_errors:
        return {
            "valid": False,
            "errors": validation_errors
        }
    
    # Calculate FRA score if valid
    fra_score = calculate_fra_score(request.trait_scores)
    
    return {
        "valid": True,
        "errors": [],
        "fra_score": float(fra_score) if fra_score else None
    }

@router.get("/officer/{officer_id}/rank-analysis/{rank}")
async def get_rank_analysis(
    officer_id: int, 
    rank: str, 
    db: Session = Depends(get_db)
):
    """
    Get detailed analysis for a specific rank within a Reporting Senior's profile.
    """
    
    officer = db.query(Officer).filter(Officer.id == officer_id).first()
    if not officer:
        raise HTTPException(status_code=404, detail="Reporting Senior not found")
    
    # Get all reports this RS has written for the specified rank
    reports = db.query(FitReport).filter(
        FitReport.reporting_senior_name == f"{officer.last_name}, {officer.first_name}",
        FitReport.rank_at_time == rank
    ).order_by(FitReport.report_date).all()
    
    if not reports:
        raise HTTPException(status_code=404, detail=f"No reports found for rank {rank}")
    
    # Get relative values
    analysis_data = []
    for report in reports:
        rv_record = db.query(RelativeValue).filter(RelativeValue.fitrep_id == report.id).first()
        
        analysis_data.append({
            "fitrep_id": report.fitrep_id,
            "report_date": str(report.report_date),
            "period": f"{report.period_from} to {report.period_to}",
            "fra_score": float(report.fra_score) if report.fra_score else None,
            "relative_value": rv_record.relative_value if rv_record else None,
            "reporting_senior": report.reporting_senior_name,
            "organization": report.organization,
            "occasion_type": report.occasion_type
        })
    
    # Group by reporting senior for RV context
    rs_groups = {}
    for data in analysis_data:
        rs_name = data["reporting_senior"] or "Unknown"
        if rs_name not in rs_groups:
            rs_groups[rs_name] = []
        rs_groups[rs_name].append(data)
    
    # Calculate statistics (exclude EN reports from averages)
    non_en_data = [d for d in analysis_data if d.get("occasion_type", "").upper() != "EN"]
    fra_scores = [d["fra_score"] for d in non_en_data if d["fra_score"] is not None]
    rv_values = [d["relative_value"] for d in non_en_data if d["relative_value"] is not None]
    
    return {
        "rank": rank,
        "total_reports": len(reports),
        "fra_statistics": {
            "average": sum(fra_scores) / len(fra_scores) if fra_scores else 0,
            "highest": max(fra_scores) if fra_scores else 0,
            "lowest": min(fra_scores) if fra_scores else 0
        },
        "rv_statistics": {
            "average": sum(rv_values) / len(rv_values) if rv_values else None,
            "highest": max(rv_values) if rv_values else None,
            "lowest": min(rv_values) if rv_values else None
        },
        "reporting_senior_breakdown": rs_groups,
        "all_reports": analysis_data
    }