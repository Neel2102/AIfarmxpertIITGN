#!/usr/bin/env python3
"""
FarmXpert Startup Script
Run this to start the FarmXpert API server
"""

import os
import sys
import subprocess
from pathlib import Path

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ .env file not found!")
        print("📝 Creating .env file with default values...")
        
        env_content = """# FarmXpert Environment Configuration

# API Configuration
APP_NAME=FarmXpert API
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000

# Gemini API Configuration
GEMINI_API_KEY=your-gemini-api-key-here

# Database Configuration (Optional)
DATABASE_URL=postgresql://user:password@localhost:5432/farmxpert
REDIS_URL=redis://localhost:6379/0
"""
        
        with open(".env", "w") as f:
            f.write(env_content)
        
        print("✅ .env file created!")
        print("⚠️  Please edit .env file and add your GEMINI_API_KEY")
        return False
    
    # Check if GEMINI_API_KEY is set
    with open(".env", "r") as f:
        content = f.read()
        if "GEMINI_API_KEY=your-gemini-api-key-here" in content:
            print("⚠️  Please set your GEMINI_API_KEY in the .env file")
            return False
    
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting FarmXpert API server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API docs will be available at: http://localhost:8000/docs")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "interfaces.api.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 FarmXpert server stopped!")
    except subprocess.CalledProcessError:
        print("❌ Failed to start server")

def main():
    """Main startup function"""
    print("🌾 Welcome to FarmXpert!")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("interfaces/api/main.py").exists():
        print("❌ Please run this script from the farmxpert directory")
        sys.exit(1)
    
    # Check environment
    if not check_env_file():
        print("\n📋 Next steps:")
        print("1. Edit .env file and add your GEMINI_API_KEY")
        print("2. Run this script again")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()
