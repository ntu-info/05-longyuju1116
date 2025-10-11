#!/usr/bin/env python3
"""
Test script for Neurosynth Backend API endpoints.

Usage:
    python test_endpoints.py https://ns-nano.onrender.com
"""

import sys
import requests
from typing import Optional


def test_endpoint(base_url: str, path: str, description: str) -> bool:
    """
    Test a single endpoint.
    
    Args:
        base_url: Base URL of the API
        path: Endpoint path
        description: Description of the test
        
    Returns:
        True if test passed, False otherwise
    """
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # Try to parse as JSON
            try:
                data = response.json()
                print(f"Response (JSON):")
                import json
                print(json.dumps(data, indent=2, default=str)[:500])
                if len(json.dumps(data, default=str)) > 500:
                    print("... (truncated)")
                print(f"✅ PASS: {description}")
                return True
            except ValueError:
                # Not JSON, show raw text
                print(f"Response (TEXT): {response.text[:200]}")
                print(f"✅ PASS: {description}")
                return True
        else:
            print(f"Response: {response.text[:200]}")
            print(f"❌ FAIL: {description}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    """Run all endpoint tests."""
    if len(sys.argv) < 2:
        print("Usage: python test_endpoints.py <BASE_URL>")
        print("Example: python test_endpoints.py https://ns-nano.onrender.com")
        sys.exit(1)
    
    base_url = sys.argv[1]
    print(f"\n{'#'*60}")
    print(f"# Neurosynth Backend API Test Suite")
    print(f"# Base URL: {base_url}")
    print(f"{'#'*60}")
    
    tests = [
        ("/", "Health check"),
        ("/img", "Static image file"),
        ("/test_db", "Database connectivity test"),
        (
            "/dissociate/terms/fear/pain",
            "Dissociate by terms (fear \\ pain) - with auto prefix"
        ),
        (
            "/dissociate/terms/pain/fear",
            "Dissociate by terms (pain \\ fear) - with auto prefix"
        ),
        (
            "/dissociate/locations/0_-52_26/-2_50_-6",
            "Dissociate by locations (PCC \\ vmPFC) - default radius=6mm"
        ),
        (
            "/dissociate/locations/-2_50_-6/0_-52_26",
            "Dissociate by locations (vmPFC \\ PCC) - default radius=6mm"
        ),
        (
            "/dissociate/locations/0_-52_26/-2_50_-6/10",
            "Dissociate by locations (PCC \\ vmPFC) - custom radius=10mm"
        ),
        (
            "/dissociate/locations/0_-52_26/-2_50_-6/8",
            "Dissociate by locations (PCC \\ vmPFC) - custom radius=8mm"
        ),
        (
            "/locations/0_-52_26/6",
            "Studies near coordinate [0, -52, 26] with radius=6mm"
        ),
        (
            "/locations/-2_50_-6/10",
            "Studies near coordinate [-2, 50, -6] with radius=10mm"
        ),
    ]
    
    results = []
    for path, description in tests:
        passed = test_endpoint(base_url, path, description)
        results.append((description, passed))
    
    # Summary
    print(f"\n{'#'*60}")
    print(f"# Test Summary")
    print(f"{'#'*60}")
    
    passed = sum(1 for _, p in results if p)
    total = len(results)
    
    for desc, p in results:
        status = "✅ PASS" if p else "❌ FAIL"
        print(f"{status}: {desc}")
    
    print(f"\n{'='*60}")
    print(f"Total: {passed}/{total} tests passed")
    print(f"{'='*60}")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

