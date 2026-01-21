"""
Test script for the Analytical API
Task 4 - Build an Analytical API
"""
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_endpoint(name: str, url: str, params: Dict[str, Any] = None) -> bool:
    """Test an API endpoint"""
    print(f"\n{'='*70}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    if params:
        print(f"Params: {params}")
    print('='*70)
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response (first 500 chars):")
            print(json.dumps(data, indent=2, default=str)[:500])
            if len(json.dumps(data, default=str)) > 500:
                print("... (truncated)")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to API. Is the server running?")
        print("Start the server with: python scripts/run_api.py")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    print("="*70)
    print("MEDICAL TELEGRAM WAREHOUSE API - TEST SUITE")
    print("="*70)
    print("\nMake sure the API server is running:")
    print("  python scripts/run_api.py")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    input()
    
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", test_endpoint(
        "Health Check",
        f"{BASE_URL}/health"
    )))
    
    # Test 2: Root endpoint
    results.append(("Root Endpoint", test_endpoint(
        "Root Endpoint",
        f"{BASE_URL}/"
    )))
    
    # Test 3: Top Products
    results.append(("Top Products", test_endpoint(
        "Top Products",
        f"{BASE_URL}/api/reports/top-products",
        {"limit": 5}
    )))
    
    # Test 4: Channel Activity
    results.append(("Channel Activity", test_endpoint(
        "Channel Activity",
        f"{BASE_URL}/api/channels/chemed123/activity"
    )))
    
    # Test 5: Search Messages
    results.append(("Search Messages", test_endpoint(
        "Search Messages",
        f"{BASE_URL}/api/search/messages",
        {"query": "medicine", "limit": 5}
    )))
    
    # Test 6: Visual Content Stats
    results.append(("Visual Content Stats", test_endpoint(
        "Visual Content Stats",
        f"{BASE_URL}/api/reports/visual-content"
    )))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
