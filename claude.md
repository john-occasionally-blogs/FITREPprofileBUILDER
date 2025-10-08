# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FITREP Assistance Tool is a containerized web application for processing Marine Corps FITREP (Fitness Report) PDFs. It calculates fitness report averages (FRA) and relative values (RV) for Marine officers, and predicts the impact of new reports on officer profiles.

**Technology Stack:**
- Frontend: React 18.2 with TypeScript, React Router, react-dropzone
- Backend: FastAPI (Python) with SQLAlchemy ORM
- PDF Processor: Standalone FastAPI service with PyMuPDF and Pytesseract OCR
- Database: PostgreSQL 15
- Containerization: Docker Compose

## Running the Application

All services run through Docker Compose:

```bash
# Start all services (frontend, backend, pdf-processor, database)
docker-compose up --build

# Stop all services
docker-compose down

# View logs for specific service
docker-compose logs frontend
docker-compose logs backend
docker-compose logs pdf-processor
docker-compose logs database
```

**Service URLs:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PDF Processor: http://localhost:8001

## Development Commands

**Frontend (React):**
```bash
cd frontend
npm start          # Development server
npm test           # Run tests
npm run build      # Production build
```

**Backend (FastAPI):**
Backend runs via Docker. For database operations:
```bash
# Reset database (from backend directory)
python reset_db.py

# Initialize database
python init_db.py
```

**Testing with SQLite:**
The root directory contains standalone Python scripts for testing extraction logic without Docker:
- `fitrep_extractor.py` - Main OCR extraction logic
- `simple_demo.py` - Test extraction with SQLite
- `demo_app.py` - Demo Flask app
- `test_setup.py` - Database setup tests

## Architecture Overview

### Service Architecture
The application uses a microservices architecture with 4 Docker containers:
1. **Frontend** - React SPA serving the UI
2. **Backend** - FastAPI REST API handling business logic and database operations
3. **PDF Processor** - Isolated OCR service for FITREP extraction
4. **Database** - PostgreSQL with persistent volume

### Data Flow
1. User uploads FITREP PDFs via frontend
2. Frontend sends files to backend `/api/fitreports/auto-upload`
3. Backend extracts officer info from first PDF using `fitrep_extractor.py`
4. Backend creates/retrieves Officer record
5. All PDFs processed through PDF processor service
6. Backend calculates FRA scores from trait scores
7. Backend calculates RV (Relative Value) scores using `calculate_relative_values()`
8. Results stored in database and returned to frontend

### Database Models
Key models in `backend/app/models/models.py`:
- **Officer** - Marine officer identity (service_number, name, rank)
- **FitReport** - Individual FITREP with dates, organization, FRA score
- **TraitScore** - 14 trait scores (A-G or H for non-observed) per FITREP
- **RelativeValue** - RV calculation (80-100 scale) per FITREP
- **Profile** - Aggregated statistics for reporting senior
- **ScoringSession** - What-if scenario predictions

### Scoring Algorithm
Core logic in `backend/app/utils/scoring.py`:

**FRA Calculation:**
- Each of 14 traits scored A-G (A=1, B=2, ..., G=7)
- H = Non-observed (excluded from calculation)
- FRA = Average of all scorable traits
- Function: `calculate_fra_score(trait_scores: Dict[str, str])`

**RV Calculation:**
- Requires minimum 3 reports from same reporting senior for same rank
- RV 100 = Highest FRA for rank/RS combination
- RV 90 = Average FRA for rank/RS combination
- RV 80 = Average - (Highest - Average), serves as floor
- Linear interpolation between anchor points
- Function: `calculate_relative_values(fra_scores: List[Tuple], rank: str, reporting_senior: str)`

**EN Report Handling:**
- EN (Enlisted) occasion type reports are displayed but excluded from FRA/RV averages
- Logic in `backend/app/api/profiles.py:139` filters EN reports from statistics

### Frontend Routing
Routes defined in `frontend/src/App.tsx`:
- `/` - HomePage: Select action (create/view/update profile)
- `/create-profile` - CreateProfilePage: Upload PDFs to create new profile
- `/profile/:officerId` - ProfileViewPage: View reporting senior's profile with rank breakdown
- `/update-profile/:officerId` - UpdateProfilePage: Add more FITREPs to existing profile
- `/data-review` - DataReviewPage: Review extracted data

### API Endpoints
Main routers in `backend/app/main.py`:
- `/api/officers/*` - Officer CRUD operations
- `/api/fitreports/*` - FITREP upload, processing, retrieval
- `/api/profiles/*` - Profile views and statistics
- `/api/scoring/*` - RV calculations and what-if scenarios

**Key Endpoints:**
- `POST /api/fitreports/auto-upload` - Upload PDFs, auto-extract officer data, create profile
- `GET /api/profiles/{officer_id}` - Get complete profile for reporting senior
- `POST /api/scoring/predict-impact` - Calculate impact of hypothetical new FITREPs

### OCR Extraction
The `fitrep_extractor.py` uses multi-method extraction:
1. **PyMuPDF text extraction** - Fastest, works on digital PDFs
2. **Pytesseract OCR** - Fallback for scanned PDFs
3. **Positional OCR** - Uses `image_to_data()` to find values near labels
4. **Multi-page processing** - Page 1 for admin data, Page 2 for trait scores

**Grade Extraction:**
- Validates against `valid_grades` list (SGT-GEN ranks)
- Normalizes tokens but preserves digits (1STLT, 2NDLT)
- Function: `normalize_grade_token()` vs `normalize_token()`

**Trait Score Extraction:**
- Searches for 14 standard trait names
- Extracts letter grades A-H using positional data
- Handles multi-word trait names with fuzzy matching

## Important Notes

**Security:**
- Application designed for sensitive military data
- All processing occurs locally (no external connections)
- PDFs deleted after extraction (only data stored)
- Database credentials in `docker-compose.yml` for local dev only

**Rank Ordering:**
- System supports all Marine ranks (enlisted, warrant, officer, general)
- Rank hierarchy defined in `RANK_ORDER` dict in `scoring.py`
- Lower number = higher rank (GEN=1, SGT=22)

**Profile View Context:**
- Profile endpoint (`/api/profiles/{officer_id}`) returns data WHERE the officer is the Reporting Senior
- "Marines" list shows all Marines this RS has written FITREPs for
- Rank breakdown groups reports by Marine rank, not RS rank

**Decimal Precision:**
- FRA scores use `Decimal` type with 2 decimal places
- Must convert to `float` for JSON serialization
- Rounding uses `ROUND_HALF_UP` for consistency

**Development Files:**
- `fitrep_extractor.py` in root is the canonical extraction logic
- Duplicated in `pdf-processor/app/services/fitrep_extractor.py` for service isolation
- Changes to extraction should be made in root file first, then copied to service
