#!/usr/bin/env python3
"""
Test Elasticsearch connections for debugging
"""
from elasticsearch import Elasticsearch
import requests

def test_direct_http():
    """Test direct HTTP connection"""
    try:
        response = requests.get("http://localhost:9200")
        print("✅ Direct HTTP connection successful:")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Direct HTTP connection failed: {e}")
        return False

def test_es_client():
    """Test Elasticsearch client connection"""
    # Try different connection configurations
    configs = [
        {
            "name": "Basic HTTP",
            "config": {"hosts": ["http://localhost:9200"]}
        },
        {
            "name": "With explicit settings",
            "config": {
                "hosts": ["http://localhost:9200"],
                "verify_certs": False,
                "ssl_show_warn": False
            }
        },
        {
            "name": "With API compatibility",
            "config": {
                "hosts": ["http://localhost:9200"],
                "verify_certs": False,
                "ssl_show_warn": False,
                "api_key": None,
                "basic_auth": None
            }
        }
    ]
    
    for config_test in configs:
        try:
            print(f"\n   Testing {config_test['name']}:")
            es = Elasticsearch(**config_test['config'])
            
            if es.ping():
                print("   ✅ Connection successful")
                info = es.info()
                print(f"      Cluster: {info['cluster_name']}")
                print(f"      Version: {info['version']['number']}")
                return es, True
            else:
                print("   ❌ Ping failed")
                
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
            
    return None, False

if __name__ == "__main__":
    print("Testing Elasticsearch connections...")
    print("=" * 40)
    
    print("\n1. Testing direct HTTP connection:")
    test_direct_http()
    
    print("\n2. Testing Elasticsearch client:")
    working_client, success = test_es_client()
    
    if success:
        print(f"\n✅ Found working configuration!")
    else:
        print(f"\n❌ No working Elasticsearch client configuration found")