import PyPDF2
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import re
from typing import Dict, Optional, List
from datetime import datetime

class FitrepExtractor:
    """
    Extracts data from Marine Corps FITREP PDF files (NAVMC 10835B).
    Handles both text-based PDFs and scanned image PDFs using OCR.
    """
    
    def __init__(self):
        self.trait_patterns = {
            "Mission Accomplishment": r"MISSION ACCOMPLISHMENT.*?([A-H])\s*(?:\[X\]|\☐)",
            "Proficiency": r"PROFICIENCY.*?([A-H])\s*(?:\[X\]|\☐)",
            "Individual Character": r"INDIVIDUAL CHARACTER.*?([A-H])\s*(?:\[X\]|\☐)",
            "Effectiveness Under Stress": r"EFFECTIVENESS UNDER STRESS.*?([A-H])\s*(?:\[X\]|\☐)",
            "Initiative": r"INITIATIVE.*?([A-H])\s*(?:\[X\]|\☐)",
            "Leadership": r"LEADERSHIP.*?([A-H])\s*(?:\[X\]|\☐)",
            "Developing Subordinates": r"DEVELOPING SUBORDINATES.*?([A-H])\s*(?:\[X\]|\☐)",
            "Setting the Example": r"SETTING THE EXAMPLE.*?([A-H])\s*(?:\[X\]|\☐)",
            "Ensuring Well-being": r"ENSURING WELL-BEING.*?([A-H])\s*(?:\[X\]|\☐)",
            "Communication Skills": r"COMMUNICATION SKILLS.*?([A-H])\s*(?:\[X\]|\☐)",
            "Intellect and Wisdom": r"INTELLECT AND WISDOM.*?([A-H])\s*(?:\[X\]|\☐)",
            "Decision Making": r"DECISION MAKING.*?([A-H])\s*(?:\[X\]|\☐)",
            "Judgment": r"JUDGMENT.*?([A-H])\s*(?:\[X\]|\☐)",
            "Fulfillment of Evaluation": r"FULFILLMENT OF EVALUATION.*?([A-H])\s*(?:\[X\]|\☐)"
        }
    
    async def extract_fitrep_data(self, pdf_path: str) -> Dict:
        """
        Extract FITREP data from PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary containing extracted FITREP data
        """
        try:
            # First, try to extract text directly from PDF
            text_content = self._extract_text_from_pdf(pdf_path)
            
            # If text extraction failed or returned minimal content, use OCR
            if not text_content or len(text_content.strip()) < 100:
                text_content = await self._extract_text_with_ocr(pdf_path)
            
            # Parse the extracted text
            return self._parse_fitrep_content(text_content)
            
        except Exception as e:
            raise Exception(f"Failed to extract FITREP data: {str(e)}")
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text directly from PDF."""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
        except Exception as e:
            print(f"Direct text extraction failed: {e}")
        
        return text
    
    async def _extract_text_with_ocr(self, pdf_path: str) -> str:
        """Extract text using OCR on PDF images."""
        try:
            # Convert PDF pages to images
            images = convert_from_path(pdf_path)
            
            full_text = ""
            for i, image in enumerate(images):
                # Use tesseract OCR to extract text
                text = pytesseract.image_to_string(image, config='--psm 6')
                full_text += f"\\n--- Page {i+1} ---\\n{text}\\n"
            
            return full_text
            
        except Exception as e:
            raise Exception(f"OCR extraction failed: {str(e)}")
    
    def _parse_fitrep_content(self, content: str) -> Dict:
        """Parse extracted text content to structured FITREP data."""
        
        # Clean up content
        content = re.sub(r'\\s+', ' ', content)
        content = content.upper()  # Convert to uppercase for consistent matching
        
        extracted_data = {
            "administrative_info": self._extract_administrative_info(content),
            "trait_scores": self._extract_trait_scores(content),
            "reporting_senior_info": self._extract_reporting_senior_info(content),
            "reviewing_officer_info": self._extract_reviewing_officer_info(content),
            "extraction_metadata": {
                "extraction_date": datetime.now().isoformat(),
                "content_length": len(content),
                "method": "ocr" if "Page" in content else "direct_text"
            }
        }
        
        return extracted_data
    
    def _extract_administrative_info(self, content: str) -> Dict:
        """Extract administrative information from FITREP."""
        admin_info = {}
        
        # Extract FITREP ID
        fitrep_id_match = re.search(r'FITREP ID #?([0-9]+)', content)
        if fitrep_id_match:
            admin_info["fitrep_id"] = fitrep_id_match.group(1)
        
        # Extract name (look for patterns near "MARINE REPORTED ON")
        name_patterns = [
            r'MARINE REPORTED ON:.*?([A-Z]+),\\s*([A-Z]+)\\s*([A-Z])?',
            r'LAST NAME.*?([A-Z]+).*?FIRST NAME.*?([A-Z]+).*?MI.*?([A-Z])?'
        ]
        
        for pattern in name_patterns:
            name_match = re.search(pattern, content)
            if name_match:
                admin_info["last_name"] = name_match.group(1)
                admin_info["first_name"] = name_match.group(2)
                admin_info["middle_initial"] = name_match.group(3) if name_match.group(3) else ""
                break
        
        # Extract rank
        rank_match = re.search(r'GRADE.*?([A-Z]{2,4})', content)
        if rank_match:
            admin_info["rank"] = rank_match.group(1)
        
        # Extract dates
        date_patterns = [
            r'FROM.*?(\\d{8}).*?TO.*?(\\d{8})',
            r'PERIOD COVERED.*?(\\d{2}/\\d{2}/\\d{4}).*?(\\d{2}/\\d{2}/\\d{4})'
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, content)
            if date_match:
                admin_info["period_from"] = date_match.group(1)
                admin_info["period_to"] = date_match.group(2)
                break
        
        # Extract organization
        org_match = re.search(r'ORGANIZATION.*?([A-Z\\s]{10,50})', content)
        if org_match:
            admin_info["organization"] = org_match.group(1).strip()
        
        return admin_info
    
    def _extract_trait_scores(self, content: str) -> Dict[str, str]:
        """Extract the 14 trait scores from FITREP content."""
        trait_scores = {}
        
        # Look for checkbox patterns indicating selected scores
        # Pattern looks for trait name followed by A B C D E F G H with one marked
        for trait_name, pattern in self.trait_patterns.items():
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                trait_scores[trait_name] = match.group(1)
        
        # Alternative approach: look for specific checkbox patterns
        if len(trait_scores) < 10:  # If we didn't get enough traits, try alternative method
            trait_scores = self._extract_trait_scores_alternative(content)
        
        return trait_scores
    
    def _extract_trait_scores_alternative(self, content: str) -> Dict[str, str]:
        """Alternative method to extract trait scores using different patterns."""
        trait_scores = {}
        
        # Split content by sections and look for scoring patterns
        sections = re.split(r'[DEF]\\.|SECTION|PART', content)
        
        for section in sections:
            # Look for patterns like "A [X] B [ ] C [ ]" etc.
            checkbox_patterns = re.findall(r'([A-H])\\s*(?:\\[X\\]|☑|✓)', section)
            
            # Try to match these to trait sections
            if 'MISSION' in section and 'ACCOMPLISHMENT' in section:
                if checkbox_patterns:
                    trait_scores["Mission Accomplishment"] = checkbox_patterns[0]
            elif 'PROFICIENCY' in section:
                if checkbox_patterns:
                    trait_scores["Proficiency"] = checkbox_patterns[0]
            # Add more specific trait matching as needed
        
        return trait_scores
    
    def _extract_reporting_senior_info(self, content: str) -> Dict:
        """Extract reporting senior information."""
        rs_info = {}
        
        # Look for reporting senior section
        rs_patterns = [
            r'REPORTING SENIOR.*?([A-Z]+).*?([A-Z]{2,4})',
            r'RS.*?([A-Z\\s]+).*?([A-Z]{2,4})'
        ]
        
        for pattern in rs_patterns:
            rs_match = re.search(pattern, content)
            if rs_match:
                rs_info["name"] = rs_match.group(1).strip()
                rs_info["rank"] = rs_match.group(2)
                break
        
        return rs_info
    
    def _extract_reviewing_officer_info(self, content: str) -> Dict:
        """Extract reviewing officer information."""
        ro_info = {}
        
        # Look for reviewing officer section
        ro_patterns = [
            r'REVIEWING OFFICER.*?([A-Z]+).*?([A-Z]{2,4})',
            r'RO.*?([A-Z\\s]+).*?([A-Z]{2,4})'
        ]
        
        for pattern in ro_patterns:
            ro_match = re.search(pattern, content)
            if ro_match:
                ro_info["name"] = ro_match.group(1).strip()
                ro_info["rank"] = ro_match.group(2)
                break
        
        return ro_info