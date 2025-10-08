# Marine FITREP Assistance Tool

A containerized web application for analyzing Marine Corps Fitness Reports (FITREPs). This tool helps users calculate Fitness Report Averages (FRA) and Relative Values (RV), and predict the impact of new reports on officer profiles.

## Features

- **Automated PDF Processing**: Upload FITREP PDFs and automatically extract data using OCR
- **FRA Calculation**: Calculate Fitness Report Average from trait scores (A-H scale)
- **RV Calculation**: Compute Relative Values (80-100 scale) based on reporting senior performance
- **Profile Analysis**: View comprehensive breakdowns by rank with statistics
- **Impact Prediction**: Test "what-if" scenarios to see how new reports affect profiles
- **Multi-RS Support**: Handle multiple Reporting Senior profiles in one system
- **Data Management**: Review all records and clean up extracted data

## Technology Stack

- **Frontend**: React 18.2 with TypeScript, React Router
- **Backend**: FastAPI (Python) with SQLAlchemy ORM
- **PDF Processing**: Standalone service with PyMuPDF and Pytesseract OCR
- **Database**: PostgreSQL 15
- **Containerization**: Docker Compose

## Prerequisites

- Docker Desktop (Mac/Windows) or Docker Engine + Docker Compose (Linux)
- 4GB+ RAM recommended
- Tesseract OCR (included in Docker containers)

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd vibeFITREP
   ```

2. **Start the application**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

4. **Stop the application**
   ```bash
   docker-compose down
   ```

## Usage

### Creating a Profile

1. Navigate to **Create New Profile**
2. Upload one or more FITREP PDF files
3. The system will automatically extract reporting senior information
4. Review extracted data and proceed to analysis

### Viewing Analysis

1. Select a Reporting Senior profile from the home page
2. View FRA and RV scores broken down by rank
3. See individual FITREP details with trait scores
4. Access "All Ranks" view for comprehensive statistics

### Predicting Impact

1. From a profile view, use the "Predict Impact" feature
2. Add hypothetical new FITREPs with trait scores
3. See how the new reports would affect overall statistics
4. Compare current vs. predicted FRA and RV values

### Data Management

1. Click the **Data Review** button (bottom right)
2. View all FITREPs across all profiles
3. Delete individual reports or clear entire database
4. Re-upload PDFs as needed

## Architecture

### Service Architecture

The application uses a microservices architecture with 4 Docker containers:

1. **Frontend** - React SPA serving the UI (port 3000)
2. **Backend** - FastAPI REST API (port 8000)
3. **PDF Processor** - Isolated OCR service (port 8001)
4. **Database** - PostgreSQL with persistent volume (port 5432)

### Data Flow

1. User uploads FITREP PDFs via frontend
2. Backend extracts reporting senior info from first PDF
3. Backend creates/retrieves Officer record
4. All PDFs processed through PDF processor service
5. Backend calculates FRA scores from trait scores
6. Backend calculates RV scores using relative value algorithm
7. Results stored in database and returned to frontend

### Scoring Algorithm

**FRA Calculation:**
- Each of 14 traits scored A-G (A=1, B=2, ..., G=7)
- H = Non-observed (excluded from calculation)
- FRA = Average of all scorable traits

**RV Calculation:**
- Requires minimum 3 reports from same reporting senior for same rank
- RV 100 = Highest FRA for rank/RS combination
- RV 90 = Average FRA for rank/RS combination
- RV 80 = Average - (Highest - Average), serves as floor
- Linear interpolation between anchor points

## Development

### Project Structure

```
vibeFITREP/
├── frontend/          # React TypeScript application
│   ├── src/
│   │   ├── pages/     # Page components
│   │   ├── services/  # API client
│   │   └── utils/     # Utility functions
│   └── Dockerfile
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── api/       # API endpoints
│   │   ├── models/    # Database models
│   │   └── utils/     # Business logic
│   └── Dockerfile
├── pdf-processor/     # OCR service
│   ├── app/
│   │   └── services/  # Extraction logic
│   └── Dockerfile
├── database/          # Database init scripts
├── fitrep_extractor.py # Core extraction module
└── docker-compose.yml
```

### Running Individual Services

**Frontend:**
```bash
cd frontend
npm install
npm start
```

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Database:**
```bash
docker run -p 5432:5432 -e POSTGRES_PASSWORD=fitrep_password postgres:15-alpine
```

### Testing

The root directory contains standalone Python scripts for testing:
- `fitrep_extractor.py` - Main OCR extraction logic
- `simple_demo.py` - Test extraction with SQLite
- `demo_app.py` - Demo Flask app
- `test_setup.py` - Database setup tests

## Configuration

### Environment Variables

**Backend:**
- `DATABASE_URL` - PostgreSQL connection string
- `PDF_PROCESSOR_URL` - PDF processor service URL

**Frontend:**
- `REACT_APP_BACKEND_URL` - Backend API URL

### Docker Compose

Default configuration in `docker-compose.yml`:
- Database credentials (change in production)
- Port mappings
- Volume mounts for data persistence

## Security Notes

⚠️ **Important Security Considerations:**

1. **Local Development Only**: Default database credentials are for local development. Change them in production.
2. **No External Connections**: All processing occurs locally - no data sent to external services.
3. **PDF Handling**: PDFs are deleted after extraction; only extracted data is stored.
4. **Sensitive Data**: This tool processes sensitive military performance data. Use appropriate security measures.

## Troubleshooting

### Docker Issues

**"Mounts denied" error on macOS:**
- Open Docker Desktop → Settings → Resources → File Sharing
- Add the project directory to shared paths

**Port already in use:**
```bash
# Change ports in docker-compose.yml
ports:
  - "3001:3000"  # Frontend
  - "8001:8000"  # Backend
```

### OCR Extraction Issues

**Poor extraction quality:**
- Ensure PDFs are high quality (not heavily compressed)
- Check that Tesseract is properly installed in container
- Review logs: `docker-compose logs pdf-processor`

**Missing data:**
- Verify PDF format matches expected FITREP layout
- Check extraction logs for specific field failures
- Use Data Review page to identify and fix issues

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with FastAPI, React, and PostgreSQL
- OCR powered by Tesseract and PyMuPDF
- Designed for Marine Corps FITREP analysis workflows

## Disclaimer

This is an unofficial tool and is not endorsed by or affiliated with the United States Marine Corps or Department of Defense. Use at your own discretion and in accordance with applicable regulations.

---

**For Official Use Only** - This tool processes sensitive performance evaluation data. Ensure proper handling and storage of all data in accordance with applicable security policies.
