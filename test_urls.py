#!/usr/bin/env python3
"""
Test script to verify both localhost and 127.0.0.1 work identically
"""

import requests
import json
from datetime import datetime

def test_url(url):
    """Test a specific URL and return response info"""
    try:
        print(f"\n🔍 Testing: {url}")
        
        # Test main page
        response = requests.get(url, timeout=5)
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Size: {len(response.content)} bytes")
        
        # Test health endpoint
        health_response = requests.get(f"{url}/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   Health Check: ✅ {health_data['status']}")
            print(f"   Server Host: {health_data['host']}")
        
        # Test API status
        api_response = requests.get(f"{url}/api/status", timeout=5)
        print(f"   API Status: {api_response.status_code}")
        
        return {
            'url': url,
            'main_status': response.status_code,
            'main_size': len(response.content),
            'health_status': health_response.status_code if health_response else None,
            'api_status': api_response.status_code if api_response else None,
            'success': response.status_code == 200
        }
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
        return {
            'url': url,
            'error': str(e),
            'success': False
        }

def main():
    """Test both localhost and 127.0.0.1"""
    print("🎱 Testing Snooker Detection Web App URLs")
    print("=" * 50)
    
    urls_to_test = [
        "http://localhost:5000",
        "http://127.0.0.1:5000"
    ]
    
    results = []
    for url in urls_to_test:
        result = test_url(url)
        results.append(result)
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    all_successful = True
    for result in results:
        if result['success']:
            print(f"✅ {result['url']} - Working correctly")
        else:
            print(f"❌ {result['url']} - Failed")
            all_successful = False
    
    if all_successful:
        # Check if responses are identical
        if len(results) >= 2 and results[0]['success'] and results[1]['success']:
            if results[0]['main_size'] == results[1]['main_size']:
                print("\n🎉 Both URLs return identical content!")
            else:
                print(f"\n⚠️  URLs return different content sizes:")
                print(f"   localhost: {results[0]['main_size']} bytes")
                print(f"   127.0.0.1: {results[1]['main_size']} bytes")
    
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()