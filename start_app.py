#!/usr/bin/env python3
"""
Simple startup script for VibeFITREP app
"""
import os
import sys
import subprocess
import time

def install_requirements():
    """Install Python requirements"""
    print("📦 Installing Python packages...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Python packages installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        return False

def setup_database():
    """Initialize the database"""
    print("🗄️ Setting up database...")
    try:
        # Change to backend directory
        os.chdir("backend")
        subprocess.run([sys.executable, "init_db.py"], check=True)
        print("✅ Database initialized successfully!")
        os.chdir("..")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to setup database: {e}")
        os.chdir("..")
        return False

def start_backend():
    """Start the FastAPI backend"""
    print("🚀 Starting backend server...")
    os.chdir("backend")
    # Use subprocess.Popen to start in background
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "app.main:app", 
        "--reload", "--host", "0.0.0.0", "--port", "8000"
    ])
    os.chdir("..")
    print("✅ Backend server started on http://localhost:8000")
    return process

def start_frontend():
    """Start the React frontend"""
    print("⚛️ Starting frontend...")
    if not os.path.exists("frontend/node_modules"):
        print("📦 Installing Node.js packages...")
        os.chdir("frontend")
        subprocess.run(["npm", "install"], check=True)
        os.chdir("..")
    
    os.chdir("frontend")
    process = subprocess.Popen(["npm", "start"])
    os.chdir("..")
    print("✅ Frontend started on http://localhost:3000")
    return process

def main():
    print("🎯 VibeFITREP Startup Script")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists("backend") or not os.path.exists("frontend"):
        print("❌ Please run this script from the vibeFITREP root directory")
        return
    
    # Install requirements
    if not install_requirements():
        return
    
    # Setup database
    if not setup_database():
        return
    
    # Start backend
    backend_process = start_backend()
    time.sleep(2)  # Give backend time to start
    
    print("\n🎉 App is starting!")
    print("📱 Frontend: http://localhost:3000")
    print("🔧 Backend API: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print("\n⌨️  Press Ctrl+C to stop all services")
    
    try:
        # Start frontend (this will block)
        frontend_process = start_frontend()
        
        # Wait for processes
        backend_process.wait()
        frontend_process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        backend_process.terminate()
        if 'frontend_process' in locals():
            frontend_process.terminate()

if __name__ == "__main__":
    main()