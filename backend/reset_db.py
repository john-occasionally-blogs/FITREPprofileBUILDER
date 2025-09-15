#!/usr/bin/env python3
"""
Reset/purge the database by removing all data and recreating tables.
This will fix any database inconsistencies.
"""

import os
from app.models.database import engine, Base, get_db
from app.models import models
from sqlalchemy.orm import Session

def reset_database():
    """Drop all tables and recreate them."""
    print("🗑️  Resetting database - this will remove ALL data...")
    
    # Drop all tables
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    
    # Recreate all tables
    print("Creating fresh tables...")
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database reset complete!")
    print("All data has been purged and tables recreated.")
    print("You can now create a fresh profile.")

def check_database_status():
    """Check what data exists in the database."""
    print("📊 Current database status:")
    
    db: Session = next(get_db())
    try:
        # Check officers
        officers = db.query(models.Officer).all()
        print(f"Officers: {len(officers)}")
        for officer in officers:
            print(f"  - {officer.first_name} {officer.last_name} (EDIPI: {officer.service_number})")
        
        # Check profiles  
        profiles = db.query(models.Profile).all()
        print(f"Profiles: {len(profiles)}")
        for profile in profiles:
            print(f"  - {profile.reporting_senior_name} ({profile.rank})")
            
        # Check fitreports
        fitreports = db.query(models.FitReport).all()
        print(f"FIT Reports: {len(fitreports)}")
        
    except Exception as e:
        print(f"Error checking database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        check_database_status()
    else:
        print("VibeFITREP Database Reset Tool")
        print("=" * 40)
        
        # Show current status first
        check_database_status()
        
        print("\n⚠️  WARNING: This will DELETE ALL DATA in the database!")
        confirm = input("Type 'YES' to confirm reset: ")
        
        if confirm == "YES":
            reset_database()
        else:
            print("Reset cancelled.")