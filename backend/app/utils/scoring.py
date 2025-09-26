from typing import List, Dict, Tuple, Optional
from decimal import Decimal, ROUND_HALF_UP

# FITREP scoring constants
LETTER_TO_NUMERIC = {
    'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7
}

# All valid FITREP ranks
VALID_RANKS = [
    # Enlisted
    'SGT', 'SSGT', 'GYSGT', 'MSGT', 'MGYSGT', '1STSGT', 'SGTMAJ',
    # Officers
    '2NDLT', '1STLT', 'CAPT', 'MAJ', 'LTCOL', 'COL',
    # Warrant Officers  
    'WO', 'CWO2', 'CWO3', 'CWO4', 'CWO5',
    # General Officers (rare but possible)
    'BGEN', 'MAJGEN', 'LTGEN', 'GEN'
]

# Rank hierarchy for sorting (lower number = higher rank)
RANK_ORDER = {
    # General Officers
    'GEN': 1, 'LTGEN': 2, 'MAJGEN': 3, 'BGEN': 4,
    # Field Grade Officers
    'COL': 5, 'LTCOL': 6, 'MAJ': 7,
    # Company Grade Officers
    'CAPT': 8, '1STLT': 9, '2NDLT': 10,
    # Warrant Officers
    'CWO5': 11, 'CWO4': 12, 'CWO3': 13, 'CWO2': 14, 'WO': 15,
    # Senior Enlisted
    'SGTMAJ': 16, '1STSGT': 17, 'MGYSGT': 18, 'MSGT': 19,
    # Junior Enlisted  
    'GYSGT': 20, 'SSGT': 21, 'SGT': 22
}

TRAIT_NAMES = [
    "Mission Accomplishment",
    "Proficiency", 
    "Individual Character",
    "Effectiveness Under Stress",
    "Initiative",
    "Leadership",
    "Developing Subordinates",
    "Setting the Example", 
    "Ensuring Well-being of Subordinates",
    "Communication Skills",
    "Intellect and Wisdom",
    "Decision Making Ability",
    "Judgment",
    "Fulfillment of Evaluation Responsibilities"
]

def calculate_fra_score(trait_scores: Dict[str, str]) -> Optional[Decimal]:
    """
    Calculate FITREP Average (FRA) from trait scores.
    
    Args:
        trait_scores: Dictionary mapping trait names to letter grades (A-G, H for non-observed)
        
    Returns:
        Decimal FRA score rounded to 2 decimal places, or None if insufficient data
    """
    numeric_scores = []
    
    for trait_name, letter_grade in trait_scores.items():
        if letter_grade == 'H':  # Non-observed, skip
            continue
        elif letter_grade in LETTER_TO_NUMERIC:
            numeric_scores.append(LETTER_TO_NUMERIC[letter_grade])
        else:
            raise ValueError(f"Invalid letter grade '{letter_grade}' for trait '{trait_name}'")
    
    if not numeric_scores:
        return None
        
    # Calculate average and round to 2 decimal places
    average = sum(numeric_scores) / len(numeric_scores)
    return Decimal(str(average)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def calculate_relative_values(fra_scores: List[Tuple[int, Decimal]], rank: str, reporting_senior: str) -> Dict[int, Dict]:
    """
    Calculate Relative Values (RV) for a set of FRA scores from the same reporting senior for the same rank.
    
    Args:
        fra_scores: List of tuples (fitrep_id, fra_score)
        rank: Military rank (e.g., "CAPT", "MAJ")
        reporting_senior: Name of reporting senior
        
    Returns:
        Dictionary mapping fitrep_id to RV data
    """
    if len(fra_scores) < 3:
        # Need at least 3 reports to calculate relative values
        return {fitrep_id: {"relative_value": None, "reason": "Insufficient reports for RV calculation"} 
                for fitrep_id, _ in fra_scores}
    
    # Sort FRA scores (higher FRA = better performance)
    sorted_scores = sorted(fra_scores, key=lambda x: x[1], reverse=True)
    
    # Calculate RV anchor points
    highest_fra = sorted_scores[0][1]  # RV 100
    
    # Calculate average FRA (RV 90)
    total_fra = sum(score for _, score in fra_scores)
    average_fra = total_fra / len(fra_scores)
    average_fra = Decimal(str(average_fra)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Calculate RV 80 threshold: Average - (Highest - Average)
    fra_80_threshold = average_fra - (highest_fra - average_fra)
    fra_80_threshold = Decimal(str(fra_80_threshold)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Assign relative values
    result = {}
    for fitrep_id, fra_score in fra_scores:
        if fra_score == highest_fra:
            rv = 100
        elif fra_score == average_fra:
            rv = 90
        elif fra_score <= fra_80_threshold:
            rv = 80  # Floor at RV 80
        else:
            # Linear interpolation between anchor points
            if fra_score > average_fra:
                # Between RV 90 and RV 100
                score_range = highest_fra - average_fra
                if score_range > 0:
                    rv_range = 10  # 100 - 90
                    score_position = fra_score - average_fra
                    rv = 90 + (rv_range * (score_position / score_range))
                else:
                    rv = 100  # If highest == average, all get 100
            else:
                # Between RV 80 and RV 90
                score_range = average_fra - fra_80_threshold
                if score_range > 0:
                    rv_range = 10  # 90 - 80
                    score_position = fra_score - fra_80_threshold
                    rv = 80 + (rv_range * (score_position / score_range))
                else:
                    rv = 90  # If average == 80 threshold, all get 90
            
            rv = max(80, min(100, int(round(rv))))  # Ensure RV is between 80-100
        
        result[fitrep_id] = {
            "relative_value": rv,
            "total_reports_for_rank": len(fra_scores),
            "highest_fra_for_rank": highest_fra,
            "average_fra_for_rank": average_fra,
            "minimum_fra_for_rank": fra_80_threshold,
            "rank": rank,
            "reporting_senior": reporting_senior
        }
    
    return result

def predict_impact(current_fra_scores: List[Decimal], new_fra_scores: List[Decimal], 
                  rank: str, reporting_senior: str, current_report_ids: List[int] = None) -> Dict:
    """
    Predict the impact of adding new FITREP scores to an existing profile.
    
    Args:
        current_fra_scores: List of current FRA scores
        new_fra_scores: List of proposed new FRA scores
        rank: Military rank
        reporting_senior: Name of reporting senior
        
    Returns:
        Dictionary with current vs. predicted metrics
    """
    # Create dummy fitrep IDs for calculation
    current_tuples = [(i, score) for i, score in enumerate(current_fra_scores)]
    combined_tuples = current_tuples + [(len(current_fra_scores) + i, score) 
                                       for i, score in enumerate(new_fra_scores)]
    
    # Calculate current RVs
    current_rvs = calculate_relative_values(current_tuples, rank, reporting_senior)
    
    # Calculate predicted RVs with new reports
    predicted_rvs = calculate_relative_values(combined_tuples, rank, reporting_senior)
    
    # Calculate metrics
    current_avg_fra = sum(current_fra_scores) / len(current_fra_scores) if current_fra_scores else 0
    combined_scores = current_fra_scores + new_fra_scores
    predicted_avg_fra = sum(combined_scores) / len(combined_scores)
    
    return {
        "current": {
            "total_reports": len(current_fra_scores),
            "average_fra": round(current_avg_fra, 2),
            "highest_fra": max(current_fra_scores) if current_fra_scores else 0,
            "lowest_fra": min(current_fra_scores) if current_fra_scores else 0,
        },
        "predicted": {
            "total_reports": len(combined_scores),
            "average_fra": round(predicted_avg_fra, 2),
            "highest_fra": max(combined_scores),
            "lowest_fra": min(combined_scores),
            "fra_change": round(predicted_avg_fra - current_avg_fra, 2)
        },
        "updated_existing_reports": [
            {
                "fitrep_id": current_report_ids[i] if current_report_ids and i < len(current_report_ids) else i,
                "index": i,
                "fra_score": float(score),
                "updated_rv": predicted_rvs[i]["relative_value"]
            } for i, score in enumerate(current_fra_scores)
        ],
        "new_reports": [
            {
                "fra_score": float(score),
                "predicted_rv": predicted_rvs[len(current_fra_scores) + i]["relative_value"]
            } for i, score in enumerate(new_fra_scores)
        ]
    }

def validate_trait_scores(trait_scores: Dict[str, str]) -> List[str]:
    """
    Validate trait scores for completeness and correctness.
    
    Args:
        trait_scores: Dictionary mapping trait names to letter grades
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Check if all required traits are present
    missing_traits = set(TRAIT_NAMES) - set(trait_scores.keys())
    if missing_traits:
        errors.append(f"Missing trait scores: {', '.join(missing_traits)}")
    
    # Check for invalid letter grades
    for trait_name, letter_grade in trait_scores.items():
        if letter_grade not in LETTER_TO_NUMERIC and letter_grade != 'H':
            errors.append(f"Invalid letter grade '{letter_grade}' for trait '{trait_name}'")
    
    # Check if all traits are non-observed (all H)
    if all(grade == 'H' for grade in trait_scores.values()):
        errors.append("All traits cannot be non-observed (H)")
    
    return errors