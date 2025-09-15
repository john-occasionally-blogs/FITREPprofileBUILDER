#!/usr/bin/env python3
"""
Test script to diagnose setup issues
"""
import sys
import os

def test_python():
    print(f"✓ Python version: {sys.version}")
    return True

def test_directory():
    expected_files = [
        'backend/app/main.py',
        'backend/app/models/models.py',
        'frontend/package.json',
        'frontend/src/App.tsx'
    ]
    
    missing_files = []
    for file in expected_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"✗ Missing files: {missing_files}")
        return False
    else:
        print("✓ All required files found")
        return True

def test_imports():
    try:
        import fastapi
        print("✓ FastAPI is available")
    except ImportError:
        print("✗ FastAPI not installed - run: pip install fastapi")
        return False
    
    try:
        import uvicorn
        print("✓ Uvicorn is available")
    except ImportError:
        print("✗ Uvicorn not installed - run: pip install uvicorn")
        return False
    
    try:
        import sqlalchemy
        print("✓ SQLAlchemy is available")
    except ImportError:
        print("✗ SQLAlchemy not installed - run: pip install sqlalchemy")
        return False
    
    return True

if __name__ == "__main__":
    print("🔍 Diagnosing VibeFITREP setup...\n")
    
    print("1. Testing Python:")
    test_python()
    
    print("\n2. Testing directory structure:")
    test_directory()
    
    print("\n3. Testing Python packages:")
    test_imports()
    
    print(f"\n📁 Current directory: {os.getcwd()}")
    print(f"📁 Directory contents: {os.listdir('.')}")