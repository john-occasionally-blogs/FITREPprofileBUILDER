#!/usr/bin/env python3
"""
Initialize the database with the required tables.
Run this script once before starting the application.
"""

from app.models.database import engine, Base
from app.models import models

def init_database():
    """Create all tables in the database."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
    print("You can now start the FastAPI server with: uvicorn app.main:app --reload")

if __name__ == "__main__":
    init_database()