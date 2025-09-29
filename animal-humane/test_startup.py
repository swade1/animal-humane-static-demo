#!/usr/bin/env python3
"""
Test script to isolate startup issues
"""
import sys

print("Testing imports...")

try:
    print("1. Testing basic imports...")
    from datetime import datetime
    from typing import List, Dict, Any
    import traceback
    print("   ✅ Basic imports OK")
    
    print("2. Testing FastAPI imports...")
    from fastapi import FastAPI, HTTPException, Depends, status, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import PlainTextResponse, JSONResponse
    from pydantic import BaseModel
    print("   ✅ FastAPI imports OK")
    
    print("3. Testing Elasticsearch imports...")
    from shelterdog_tracker.elasticsearch_handler import ElasticsearchHandler
    print("   ✅ Elasticsearch handler import OK")
    
    print("4. Testing Elasticsearch connection...")
    handler = ElasticsearchHandler(host="http://localhost:9200", index_name="animal-humane-latest")
    print("   ✅ Handler created")
    
    # This is where it might hang
    print("5. Testing Elasticsearch ping...")
    result = handler.es.ping()
    print(f"   ✅ Elasticsearch ping result: {result}")
    
    print("6. Testing scraper imports...")
    from shelterdog_tracker.shelter_scraper import ShelterScraper
    print("   ✅ Scraper import OK")
    
    print("\n🎉 All tests passed! The issue might be elsewhere.")
    
except Exception as e:
    print(f"\n❌ Error at step: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)