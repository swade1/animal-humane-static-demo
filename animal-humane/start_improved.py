#!/usr/bin/env python3
"""
Startup script for the improved Animal Humane API
"""
import sys
import os
import subprocess
from pathlib import Path

def check_elasticsearch():
    """Check if Elasticsearch is running"""
    try:
        import requests
        response = requests.get("http://localhost:9200", timeout=5)
        if response.status_code == 200:
            print("✅ Elasticsearch is running")
            return True
        else:
            print("❌ Elasticsearch is not responding correctly")
            return False
    except Exception as e:
        print(f"❌ Elasticsearch is not running: {e}")
        print("💡 Please start Elasticsearch first")
        return False

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_modules = [
        'fastapi',
        'uvicorn',
        'elasticsearch',
        'pydantic',
        'requests',
        'beautifulsoup4'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("📦 Install with: pip install " + " ".join(missing))
        return False
    else:
        print("✅ All dependencies are available")
        return True

def start_api():
    """Start the improved API"""
    print("🚀 Starting Animal Humane API with improved architecture...")
    try:
        # Use uvicorn to start the server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main_improved:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 API server stopped")
    except Exception as e:
        print(f"❌ Error starting API: {e}")

def main():
    print("🏥 Animal Humane API - Improved Architecture")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("main_improved.py").exists():
        print("❌ main_improved.py not found")
        print("💡 Please run this script from the animal-humane directory")
        return
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Check Elasticsearch
    if not check_elasticsearch():
        return
    
    # Start the API
    start_api()

if __name__ == "__main__":
    main()