# FITREP Assistance Tool

A containerized web application that processes Marine Corps FITREP PDFs to calculate fitness report averages and predict the impact of new reports on officer profiles.

## Quick Start

### Prerequisites
- Docker Desktop for Mac (must be installed and running)

### Run the Application

1. **Start the application:**
   ```bash
   docker-compose up --build
   ```

2. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

3. **Stop the application:**
   ```bash
   docker-compose down
   ```

### First Time Setup

The application will automatically:
- Create the PostgreSQL database
- Set up all required tables
- Start all services (frontend, backend, PDF processor, database)

## Application Features

### 4 Main Screens

1. **Home Screen** (`/`) - Select your action:
   - Create new profile
   - View existing profile  
   - Update existing profile

2. **Profile View Screen** (`/profile/:id`) - Analyze your FITREP data:
   - View performance by rank
   - See FRA and RV scores
   - Analyze individual reports

3. **Create Profile Screen** (`/create-profile`) - Initial setup:
   - Drag and drop PDF FITREP files
   - Process multiple files at once
   - Automatic profile creation

4. **Update Profile Screen** (`/update-profile/:id`) - Add reports:
   - Confirm existing profile
   - Add new FITREP files
   - Update calculations

## How It Works

### FITREP Processing
1. **PDF Upload**: Drag and drop FITREP PDF files
2. **Data Extraction**: OCR and text extraction from PDFs
3. **Score Calculation**: Calculate FRA (FITREP Average) from 14 traits
4. **Relative Value**: Calculate RV (80-100) based on reporting senior's historical scoring

### Scoring Algorithm
- **Trait Scores**: A=1, B=2, C=3, D=4, E=5, F=6, G=7 (H=Non-observed, excluded)
- **FRA Calculation**: Average of all scorable traits
- **RV Calculation**: 
  - RV 100: Highest FRA for the rank/RS combination
  - RV 90: Average FRA for the rank/RS combination
  - RV 80: Average - (Highest - Average), minimum floor

### Predictive Analysis
- Test impact of proposed new reports
- See how FRA and RV would change
- Make informed decisions before finalizing reports

## Architecture

### Services
- **Frontend**: React TypeScript application
- **Backend**: FastAPI Python service  
- **PDF Processor**: Dedicated OCR/extraction service
- **Database**: PostgreSQL with persistent storage

### Security
- All data remains local (no external connections)
- PDF files processed and deleted (only extracted data stored)
- Designed for sensitive military performance data

## Development

### Project Structure
```
vibeFITREP/
├── frontend/          # React application
├── backend/           # FastAPI service
├── pdf-processor/     # PDF extraction service
├── database/          # Database initialization
└── docker-compose.yml
```

### Adding Features
1. Backend API endpoints: `backend/app/api/`
2. Frontend pages: `frontend/src/pages/`
3. Scoring algorithms: `backend/app/utils/scoring.py`
4. Database models: `backend/app/models/models.py`

## Troubleshooting

### Common Issues

**Docker not starting:**
- Ensure Docker Desktop is running
- Check port availability (3000, 8000, 8001, 5432)

**PDF processing errors:**
- Verify PDFs are valid NAVMC 10835B forms
- Check PDF file size (large files may timeout)
- Ensure PDFs contain readable text or clear scans

**Database connection issues:**
- Wait for database to fully initialize (30-60 seconds)
- Check Docker logs: `docker-compose logs database`

### Logs
View service logs:
```bash
docker-compose logs frontend
docker-compose logs backend  
docker-compose logs pdf-processor
docker-compose logs database
```

## Support

This application is designed for Marine Corps officers to manage FITREP profiles and predict the impact of new fitness reports. All processing occurs locally for security.

For technical issues, check the logs and ensure all Docker services are running properly.