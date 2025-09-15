"""
Marine FITREP PDF Extractor adapted for the FITREP Assistance Tool
Based on the user's working fitrep_extractor27.py
"""

import re
import io
import fitz  # PyMuPDF  
import pytesseract
from PIL import Image
from typing import Dict, Optional, List, Tuple

class FitrepExtractor:
    def __init__(self):
        # Valid military grades - includes all FITREP recipients
        self.valid_grades = [
            'SGT', 'SSGT', 'GYSGT', 'MSGT', 'MGYSGT', '1STSGT', 'SGTMAJ',
            '2NDLT', '1STLT', 'CAPT', 'MAJ', 'LTCOL', 'COL',
            'WO', 'CWO2', 'CWO3', 'CWO4', 'CWO5',
            'BGEN', 'MAJGEN', 'LTGEN', 'GEN'
        ]
        # Valid OCC codes
        self.valid_occ_codes = ['GC', 'DC', 'CH', 'TR', 'CD', 'TD', 'FD', 'EN', 'CS', 'AN', 'AR', 'SA', 'RT']
        
        # Trait names in order (14 traits)
        self.trait_names = [
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

    def normalize_token(self, s: str) -> str:
        """Normalize a token for better matching"""
        return (s.strip().upper()
                .replace("0", "O")
                .replace("1", "I") 
                .replace("5", "S")
                .replace(":", "")
                .replace(".", ""))

    async def extract_fitrep_data(self, pdf_path: str) -> Dict:
        """
        Extract FITREP data from PDF file - main interface for the API
        """
        try:
            data = self.extract_from_pdf(pdf_path)
            
            if data is None:
                raise Exception("Could not extract data from PDF (possibly Not Observed)")
            
            # Convert to the format expected by the API
            return self.format_for_api(data)
            
        except Exception as e:
            raise Exception(f"Failed to extract FITREP data: {str(e)}")

    def extract_from_pdf(self, pdf_path: str) -> Optional[Dict]:
        """Extract required data from a single PDF file using OCR"""
        try:
            data = {}
            
            # Open PDF with PyMuPDF
            doc = fitz.open(str(pdf_path))
            
            # Process Page 1 for administrative data
            if len(doc) > 0:
                page = doc[0]
                # Higher resolution for better OCR
                mat = fitz.Matrix(3, 3)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                # Perform OCR on page 1
                text1 = pytesseract.image_to_string(img)
                
                # Get OCR with position data for better extraction
                ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                
                # Extract administrative information
                data.update(self.extract_administrative_info(text1, ocr_data, page, img))
                
                # Check for Not Observed
                not_observed = self.check_not_observed(img, text1)
                if not_observed:
                    print(f"  Skipping {pdf_path} - Not Observed is checked")
                    doc.close()
                    return None
            
            # Extract trait scores from pages 2-4 using improved text-based checkbox extraction
            trait_scores = {}
            
            # Process Page 2 - 5 traits (traits 1-5)
            if len(doc) > 1:
                page2_values = self.extract_checkbox_values_text_based(doc, 1, 5)
                for i, value in enumerate(page2_values):
                    if i < len(self.trait_names):
                        trait_scores[self.trait_names[i]] = self.number_to_letter(value)
            
            # Process Page 3 - 5 traits (traits 6-10)
            if len(doc) > 2:
                page3_values = self.extract_checkbox_values_text_based(doc, 2, 5)
                for i, value in enumerate(page3_values):
                    trait_index = i + 5
                    if trait_index < len(self.trait_names):
                        trait_scores[self.trait_names[trait_index]] = self.number_to_letter(value)
            
            # Process Page 4 - 4 traits (traits 11-14)
            if len(doc) > 3:
                page4_values = self.extract_checkbox_values_text_based(doc, 3, 4)
                for i, value in enumerate(page4_values):
                    trait_index = i + 10
                    if trait_index < len(self.trait_names):
                        trait_scores[self.trait_names[trait_index]] = self.number_to_letter(value)
            
            data['trait_scores'] = trait_scores
            doc.close()
            
            return data
            
        except Exception as e:
            print(f"Error processing {pdf_path}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def extract_administrative_info(self, text1: str, ocr_data: Dict, page, img: Image) -> Dict:
        """Extract administrative information from page 1"""
        admin_data = {}
        
        # Extract Last Name
        patterns = [
            r'Last\s+Name[:\s]*\n*([A-Z][A-Z]+)',
            r'a\.\s*Last\s+Name[:\s]*\n*([A-Z][A-Z]+)',
            r'Last Name.*?\n\s*([A-Z]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text1, re.IGNORECASE | re.MULTILINE)
            if match:
                admin_data['last_name'] = match.group(1).upper()
                break
        
        # Extract Grade using the same logic as the working extractor
        grade_value = self.extract_grade(ocr_data, img)
        if grade_value:
            admin_data['rank'] = grade_value
        
        # Extract OCC using text blocks
        occ_value = self.extract_occ(page)
        if occ_value:
            admin_data['occasion_type'] = occ_value
        
        # Extract dates
        dates = self.extract_dates(page)
        if dates:
            admin_data.update(dates)
        
        return admin_data

    def extract_grade(self, ocr_data: Dict, img: Image) -> Optional[str]:
        """Extract grade using the same logic as the working extractor"""
        grade_value = None
        top_third_height = img.height // 3
        
        # Method 1: Look for valid grades anywhere in top third
        all_top_third_tokens = []
        for i, text in enumerate(ocr_data["text"]):
            if text and ocr_data["top"][i] < top_third_height:
                tok = self.normalize_token(text)
                all_top_third_tokens.append(tok)
                # Direct match
                if tok in self.valid_grades:
                    if not grade_value:  # Take first valid grade found
                        grade_value = tok
        
        # Method 2: Look for partial matches that might be grades
        if not grade_value:
            grade_mapping = {
                'MAJ': ['MAJ', 'MAS', 'MA', 'MJ', 'MAJOR', 'MAI', 'MAT'],
                'LTCOL': ['LTCOL', 'LRCOL', 'LTCO', 'LTC', 'LTCL', 'LICOL', 'IRCOL'],
                'MGYSGT': ['MGYSGT', 'MGYST', 'MGSG', 'MGYSG', 'MGYSGI'],
                'MSGT': ['MSGT', 'SCR', 'MSG', 'MSGI', 'MST'],
                'GYSGT': ['GYSGT', 'GYSG', 'GYST', 'GSGT'],
                'SSGT': ['SSGT', 'SSG', 'SSGI', 'SST'],
                '1STSGT': ['1STSGT', 'ISTSGT', '1STSG', 'ISTSG'],
                'SGTMAJ': ['SGTMAJ', 'SGTMA', 'SGMAJ', 'SGTMAS'],
                'CAPT': ['CAPT', 'CAP', 'CAPU', 'CAPI'],
                '2NDLT': ['2NDLT', '2NDL', '2NDLI', '2ND'],
                '1STLT': ['1STLT', '1STL', '1STLI', '1ST']
            }
            
            for correct_grade, variations in grade_mapping.items():
                if correct_grade in self.valid_grades:
                    for variation in variations:
                        if variation in all_top_third_tokens:
                            grade_value = correct_grade
                            break
                    if grade_value:
                        break
        
        return grade_value

    def extract_occ(self, page) -> Optional[str]:
        """Extract OCC code from page using text blocks"""
        blocks = page.get_text("blocks")
        
        for i, block in enumerate(blocks):
            if len(block) >= 5:
                x0, y0, x1, y1, text = block[:5]
                text_lines = text.strip().split('\n')
                
                # Look for blocks containing form data
                has_form_data = any(
                    any(name in line.strip().upper() for name in ['DOE', 'JOHN']) or
                    (line.strip().isdigit() and len(line.strip()) == 8)
                    for line in text_lines
                )
                
                if has_form_data:
                    # Look for OCC codes in this block
                    for line in text_lines:
                        line_clean = line.strip().upper()
                        
                        if line_clean in self.valid_occ_codes:
                            return line_clean
                        
                        normalized = self.normalize_token(line_clean)
                        if normalized in self.valid_occ_codes:
                            return normalized
        
        return None

    def extract_dates(self, page) -> Dict:
        """Extract from and to dates from page"""
        blocks = page.get_text("blocks")
        dates_info = {}
        
        for i, block in enumerate(blocks):
            if len(block) >= 5:
                x0, y0, x1, y1, text = block[:5]
                text_lines = text.strip().split('\n')
                
                # Look for blocks with dates
                dates_found = []
                has_occ_context = False
                
                for line in text_lines:
                    line_clean = line.strip()
                    
                    if line_clean in self.valid_occ_codes:
                        has_occ_context = True
                    
                    if re.match(r'^\d{8}$', line_clean):
                        dates_found.append(line_clean)
                
                # If this block has OCC context and dates, process them
                if has_occ_context and dates_found:
                    if len(dates_found) >= 2:
                        dates_info['period_from'] = dates_found[0]
                        dates_info['period_to'] = dates_found[1]
                        break
                    elif len(dates_found) == 1:
                        dates_info['period_to'] = dates_found[0]
        
        return dates_info

    def check_not_observed(self, img: Image, text: str) -> bool:
        """Check if Not Observed checkbox is marked"""
        if 'Not Observed' in text:
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if 'Not Observed' in line:
                    check_lines = lines[i:i+3]
                    for check_line in check_lines:
                        if 'X' in check_line and 'Extended' not in check_line:
                            if len(check_line) < 50:
                                return True
        return False

    def extract_checkbox_values_text_based(self, pdf_doc, page_num: int, expected_count: int) -> List[int]:
        """Extract checkbox values using direct PDF text extraction"""
        if page_num >= len(pdf_doc):
            return [4] * expected_count
        
        page = pdf_doc[page_num]
        blocks = page.get_text("blocks")
        
        # Find X marks - they should be in separate blocks
        x_marks = []
        
        for i, block in enumerate(blocks):
            if len(block) >= 5:
                x0, y0, x1, y1, text = block[:5]
                
                # Look for isolated X marks
                text_clean = text.strip()
                if text_clean == "X":
                    x_marks.append({
                        "text": text_clean,
                        "x": (x0 + x1) / 2,  # Center X
                        "y": (y0 + y1) / 2,  # Center Y
                        "block_idx": i
                    })
        
        if not x_marks:
            return [4] * expected_count
        
        # Sort by Y position (top to bottom)
        x_marks.sort(key=lambda x: x["y"])
        
        # Group into rows by Y position
        rows = []
        if x_marks:
            current_row = [x_marks[0]]
            
            for x_mark in x_marks[1:]:
                if abs(x_mark["y"] - current_row[0]["y"]) < 30:
                    current_row.append(x_mark)
                else:
                    rows.append(current_row)
                    current_row = [x_mark]
            
            if current_row:
                rows.append(current_row)
        
        # Convert to values
        values = []
        
        for row_idx in range(expected_count):
            if row_idx < len(rows):
                row_x_marks = rows[row_idx]
                
                if row_x_marks:
                    x_pos = row_x_marks[0]["x"]
                    
                    # Position mapping to column values (A=1, B=2, C=3, D=4, E=5, F=6, G=7, H=8)
                    if x_pos < 180:
                        column = 3  # C
                    elif x_pos < 250:
                        column = 4  # D
                    elif x_pos < 340:
                        column = 5  # E
                    elif x_pos < 440:
                        column = 6  # F
                    elif x_pos < 520:
                        column = 7  # G
                    elif x_pos < 600:
                        column = 8  # H
                    elif x_pos < 700:
                        column = 2  # B
                    else:
                        column = 1  # A
                    
                    values.append(column)
                else:
                    values.append(4)  # Default to D
            else:
                values.append(4)  # Default to D
        
        return values

    def number_to_letter(self, num: int) -> str:
        """Convert numeric score to letter grade"""
        mapping = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F', 7: 'G', 8: 'H'}
        return mapping.get(num, 'D')

    def format_for_api(self, data: Dict) -> Dict:
        """Format extracted data for the API response"""
        return {
            "administrative_info": {
                "last_name": data.get('last_name', ''),
                "rank": data.get('rank', ''),
                "period_from": data.get('period_from', ''),
                "period_to": data.get('period_to', ''),
                "occasion_type": data.get('occasion_type', 'AN'),
                "fitrep_id": data.get('fitrep_id', ''),
                "organization": data.get('organization', ''),
            },
            "trait_scores": data.get('trait_scores', {}),
            "reporting_senior_info": {
                "name": data.get('reporting_senior_name', ''),
                "rank": data.get('reporting_senior_rank', '')
            },
            "reviewing_officer_info": {
                "name": data.get('reviewing_officer_name', ''),
                "rank": data.get('reviewing_officer_rank', '')
            },
            "extraction_metadata": {
                "extraction_method": "fitrep_extractor27_adapted",
                "traits_extracted": len(data.get('trait_scores', {}))
            }
        }