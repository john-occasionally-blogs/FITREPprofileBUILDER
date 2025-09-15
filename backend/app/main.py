from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import officers, fitreports, profiles, scoring
from app.models.database import engine
from app.models import models

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FITREP Assistance Tool API",
    description="API for processing Marine Corps FITREP data and calculating performance metrics",
    version="1.0.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(officers.router, prefix="/api/officers", tags=["officers"])
app.include_router(fitreports.router, prefix="/api/fitreports", tags=["fitreports"])
app.include_router(profiles.router, prefix="/api/profiles", tags=["profiles"])
app.include_router(scoring.router, prefix="/api/scoring", tags=["scoring"])

@app.get("/")
async def root():
    return {"message": "FITREP Assistance Tool API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}