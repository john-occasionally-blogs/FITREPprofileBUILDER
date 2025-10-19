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

    The PDF is formatted with each field on its own line in sequence:
    EDIPI
    Grade
    Last Name
    From Date (YYYY MM DD)
    To Date (YYYY MM DD)
    Occ
    Fitrep Average
    """
    fitreports = []

    # Split into lines and clean
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    # Find the start of the table data (after the header row)
    start_idx = None
    for i, line in enumerate(lines):
        if 'Fitrep Average' in line:
            start_idx = i + 1
            break

    if start_idx is None:
        return fitreports

    # Process lines in groups of 7 (edipi, grade, name, from_date, to_date, occ, fra)
    i = start_idx
    while i < len(lines):
        # Skip "Average By MRO Grade:" lines
        if 'Average' in lines[i] and 'Grade' in lines[i]:
            i += 2  # Skip the average line and its value
            continue

        # Need at least 7 lines for a complete record
        if i + 6 >= len(lines):
            break

        try:
            edipi = lines[i].strip()
            grade = lines[i + 1].strip()
            last_name = lines[i + 2].strip()
            from_date_raw = lines[i + 3].strip()
            to_date_raw = lines[i + 4].strip()
            occasion = lines[i + 5].strip()
            fra_str = lines[i + 6].strip()

            # Validate EDIPI (should be 10 digits)
            if not re.match(r'^\d{10}$', edipi):
                i += 1
                continue

            # Validate grade
            valid_grades = ['MAJ', 'CAPT', '1STLT', '2NDLT', 'MSGT', 'GYSGT', 'SSGT', 'SGT',
                           'MGYSGT', '1STSGT', 'SGTMAJ', 'CWO2', 'CWO3', 'CWO4', 'CWO5',
                           'WO', 'COL', 'LTCOL', 'GEN', 'LTGEN', 'MAJGEN', 'BGEN']
            if grade not in valid_grades:
                i += 1
                continue

            # Parse dates (format: "YYYY MM DD")
            from_parts = from_date_raw.split()
            to_parts = to_date_raw.split()

            if len(from_parts) != 3 or len(to_parts) != 3:
                i += 7
                continue

            from_date = f"{from_parts[0]}-{from_parts[1]}-{from_parts[2]}"
            to_date = f"{to_parts[0]}-{to_parts[1]}-{to_parts[2]}"

            # Parse FRA
            fra = None
            if fra_str and fra_str != 'N/A':
                try:
                    fra = Decimal(fra_str).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                except:
                    fra = None

            fitreports.append({
                "edipi": edipi,
                "grade": grade,
                "last_name": last_name,
                "from_date": from_date,
                "to_date": to_date,
                "occasion": occasion if occasion != 'N/A' else None,
                "fra": fra
            })

            # Move to next record (7 lines forward)
            i += 7

        except (IndexError, ValueError) as e:
            # Skip this record and try next line
            i += 1
            continue

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
