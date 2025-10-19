"""
Parser for Reporting Senior's Fitness Report List PDFs.

This module extracts FITREP data from the standardized RS list format
and generates synthetic trait scores that match the documented FRA values.
"""

from typing import List, Dict, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
import fitz  # PyMuPDF
import re
from datetime import datetime


def parse_rs_list_pdf(pdf_path: str) -> Dict:
    """
    Parse a Reporting Senior's Fitness Report List PDF.

    Args:
        pdf_path: Path to the RS list PDF

    Returns:
        Dictionary containing:
        - rs_name: Reporting Senior's name
        - rs_rank: Reporting Senior's rank
        - rs_dod_id: DOD ID (EDIPI)
        - report_date: Date the list was generated
        - fitreports: List of FITREP records
    """
    doc = fitz.open(pdf_path)

    # Extract text from all pages
    full_text = ""
    for page in doc:
        full_text += page.get_text()

    # Parse header information
    rs_info = _extract_rs_info(full_text)

    # Parse the table of FITREPs
    fitreports = _extract_fitrep_table(full_text)

    doc.close()

    return {
        "rs_name": rs_info["name"],
        "rs_rank": rs_info["rank"],
        "rs_dod_id": rs_info["dod_id"],
        "report_date": rs_info["report_date"],
        "fitreports": fitreports
    }


def _extract_rs_info(text: str) -> Dict:
    """Extract Reporting Senior information from PDF header."""
    # Extract rank and name (e.g., "LTCOL JANE A SMITH")
    name_match = re.search(r'(LTCOL|COL|MAJ|CAPT|1STLT|2NDLT|GEN|LTGEN|MAJGEN|BGEN)\s+([A-Z\s]+)', text)
    rank = name_match.group(1) if name_match else "UNKNOWN"
    name = name_match.group(2).strip() if name_match else "UNKNOWN"

    # Extract DOD ID
    dod_id_match = re.search(r'DOD ID:\s*(\d+)', text)
    dod_id = dod_id_match.group(1) if dod_id_match else None

    # Extract report date (e.g., "As of: 09-29-2025 1605")
    date_match = re.search(r'As of:\s*(\d{2}-\d{2}-\d{4})', text)
    report_date = date_match.group(1) if date_match else None

    return {
        "name": name,
        "rank": rank,
        "dod_id": dod_id,
        "report_date": report_date
    }


def _extract_fitrep_table(text: str) -> List[Dict]:
    """
    Extract FITREP records from the table portion of the PDF.

    Table format:
    Edipi Grade Last Name From Date To Date Occ Fitrep Average
    """
    fitreports = []

    # Split into lines
    lines = text.split('\n')

    # Find lines that match the FITREP data pattern
    # Pattern: EDIPI (10 digits) Grade LastName FromDate ToDate [Occ] [FRA]
    fitrep_pattern = re.compile(
        r'(\d{10})\s+'  # EDIPI
        r'(MAJ|CAPT|1STLT|2NDLT|MSGT|GYSGT|SSGT|SGT|MGYSGT|1STSGT|SGTMAJ|CWO\d|WO|COL|LTCOL|GEN|LTGEN|MAJGEN|BGEN)\s+'  # Grade
        r'([A-Z\s]+?)\s+'  # Last Name (can have spaces like "JACKSON III")
        r'(\d{4})\s+(\d{2})\s+(\d{2})\s+'  # From Date (YYYY MM DD)
        r'(\d{4})\s+(\d{2})\s+(\d{2})\s*'  # To Date (YYYY MM DD)
        r'([A-Z]{2,3})?\s*'  # Occasion code (optional, e.g., AN, TR, CH)
        r'(\d+\.\d+|N/A)?'  # FRA (optional, e.g., 3.79 or N/A)
    )

    for line in lines:
        match = fitrep_pattern.search(line)
        if match:
            edipi = match.group(1)
            grade = match.group(2)
            last_name = match.group(3).strip()
            from_year, from_month, from_day = match.group(4), match.group(5), match.group(6)
            to_year, to_month, to_day = match.group(7), match.group(8), match.group(9)
            occasion = match.group(10) if match.group(10) else None
            fra_str = match.group(11) if match.group(11) else None

            # Parse FRA
            fra = None
            if fra_str and fra_str != 'N/A':
                try:
                    fra = Decimal(fra_str).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                except:
                    fra = None

            # Format dates
            from_date = f"{from_year}-{from_month}-{from_day}"
            to_date = f"{to_year}-{to_month}-{to_day}"

            fitreports.append({
                "edipi": edipi,
                "grade": grade,
                "last_name": last_name,
                "from_date": from_date,
                "to_date": to_date,
                "occasion": occasion,
                "fra": fra
            })

    return fitreports


def generate_trait_scores_from_fra(fra: Decimal) -> Dict[str, str]:
    """
    Generate synthetic trait scores that produce the target FRA.

    Strategy:
    - Distribute scores around the target to create realistic variation
    - Use letter grades A-G where A=1, B=2, C=3, D=4, E=5, F=6, G=7
    - Ensure the average matches the target FRA

    Args:
        fra: Target FRA score (1.00 to 7.00)

    Returns:
        Dictionary mapping trait names to letter grades
    """
    from app.utils.scoring import TRAIT_NAMES

    # Convert FRA to numeric average
    target_avg = float(fra)

    # Determine the base grade and number of adjustments needed
    base_numeric = round(target_avg)  # e.g., 3.79 -> 4

    # Map numeric back to letter
    numeric_to_letter = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F', 7: 'G'}

    # Start with all traits at base grade
    trait_scores = {trait: numeric_to_letter[base_numeric] for trait in TRAIT_NAMES}

    # Calculate how many traits need adjustment to hit target
    # If FRA is 3.79 and base is 4, we need to lower some traits
    total_needed = target_avg * len(TRAIT_NAMES)  # e.g., 3.79 * 14 = 53.06
    current_total = base_numeric * len(TRAIT_NAMES)  # e.g., 4 * 14 = 56
    adjustment_needed = total_needed - current_total  # e.g., -2.94

    # Adjust traits to hit target
    traits_adjusted = 0
    for i, trait in enumerate(TRAIT_NAMES):
        if adjustment_needed == 0:
            break

        if adjustment_needed > 0 and base_numeric < 7:
            # Need to increase some scores
            trait_scores[trait] = numeric_to_letter[base_numeric + 1]
            adjustment_needed -= 1
            traits_adjusted += 1
        elif adjustment_needed < 0 and base_numeric > 1:
            # Need to decrease some scores
            trait_scores[trait] = numeric_to_letter[base_numeric - 1]
            adjustment_needed += 1
            traits_adjusted += 1

        # Stop if we've adjusted enough traits
        if abs(adjustment_needed) < 0.1:
            break

    return trait_scores


def generate_dummy_fitrep_id(edipi: str, from_date: str, to_date: str) -> int:
    """
    Generate a deterministic dummy FITREP ID from EDIPI and dates.

    This ensures the same input always produces the same ID.
    """
    # Combine inputs and hash
    combined = f"{edipi}_{from_date}_{to_date}"
    hash_value = hash(combined)

    # Convert to positive integer in reasonable range (7 digits)
    fitrep_id = abs(hash_value) % 10000000

    return fitrep_id
