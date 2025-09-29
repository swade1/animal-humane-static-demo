#!/usr/bin/env python3
"""
Quick setup script for robust scheduling
"""
import os
import sys
import subprocess
from pathlib import Path

def check_docker():
    """Check if Docker is installed and running"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker is installed")
            
            # Check if Docker daemon is running
            result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Docker daemon is running")
                return True
            else:
                print("❌ Docker daemon is not running. Please start Docker.")
                return False
        else:
            print("❌ Docker is not installed")
            return False
    except FileNotFoundError:
        print("❌ Docker is not installed")
        return False

def setup_directories():
    """Create necessary directories"""
    dirs = ['logs', 'diff_reports', 'scheduler']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✅ Created directory: {dir_name}")

def test_diff_analyzer():
    """Test the diff analyzer"""
    try:
        from scheduler.diff_analyzer import DiffAnalyzer
        analyzer = DiffAnalyzer()
        print("✅ Diff analyzer imported successfully")
        
        # Test Elasticsearch connection
        if analyzer.handler.es.ping():
            print("✅ Elasticsearch connection successful")
            return True
        else:
            print("❌ Cannot connect to Elasticsearch")
            return False
    except Exception as e:
        print(f"❌ Error testing diff analyzer: {e}")
        return False

def main():
    print("🚀 Setting up Robust Animal Humane Scheduling")
    print("=" * 50)
    
    # Check current directory
    if not Path("main_new.py").exists():
        print("❌ Please run this script from the animal-humane directory")
        sys.exit(1)
    
    # Setup directories
    setup_directories()
    
    # Check Docker
    docker_available = check_docker()
    
    # Test components
    elasticsearch_available = test_diff_analyzer()
    
    print("\n📋 Setup Summary:")
    print("=" * 30)
    
    if docker_available and elasticsearch_available:
        print("🎉 Everything looks good! You can choose from these options:")
        print("\n1. 🐳 Docker (Recommended):")
        print("   cd deployment/docker")
        print("   docker-compose up -d")
        
        print("\n2. 🔄 Background Process:")
        print("   python scheduler/background_scheduler.py")
        
        print("\n3. 📊 Manual Diff Analysis:")
        print("   python scheduler/diff_analyzer.py")
        
    elif elasticsearch_available:
        print("✅ Elasticsearch is available")
        print("❌ Docker not available - you can still use background process")
        print("\n🔄 Run background scheduler:")
        print("   python scheduler/background_scheduler.py")
        
    else:
        print("❌ Elasticsearch not available")
        print("Please ensure Elasticsearch is running on localhost:9200")
        print("\nTo start Elasticsearch:")
        if docker_available:
            print("   cd deployment/docker")
            print("   docker-compose up elasticsearch -d")
        else:
            print("   Install and start Elasticsearch manually")
    
    print(f"\n📖 For detailed instructions, see: DEPLOYMENT_GUIDE.md")

if __name__ == "__main__":
    main()