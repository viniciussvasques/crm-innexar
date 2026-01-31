
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api"

def test_health():
    print("Testing /health...")
    resp = requests.get("http://localhost:8000/health")
    print(f"Status: {resp.status_code}, Body: {resp.json()}")
    return resp.status_code == 200

def test_onboarding_proxy():
    print("\nTesting /launch/onboarding (GET)...")
    resp = requests.get(f"{BASE_URL}/launch/onboarding")
    print(f"Status: {resp.status_code}")
    # It might return 200 with empty list or actual data
    return resp.status_code == 200

def test_site_contracts_sign():
    print("\nTesting /site-contracts/sign (POST)...")
    # This requires a valid order_id. We'll try with 999999 to see if it catches the 404/error properly
    data = {
        "order_id": 999999,
        "content": "Test contract content",
        "signed_name": "Test User",
        "language": "en"
    }
    resp = requests.post(f"{BASE_URL}/site-contracts/sign", json=data)
    print(f"Status: {resp.status_code}, Body: {resp.text[:200]}")
    # We expect 404 or success if order exists. 
    # But 500 would be bad.
    return resp.status_code in [200, 404]

if __name__ == "__main__":
    success = True
    if not test_health(): success = False
    if not test_onboarding_proxy(): success = False
    if not test_site_contracts_sign(): success = False
    
    if success:
        print("\n✓ All API tests passed (or handled expected errors)")
    else:
        print("\n✗ Some API tests failed")
        sys.exit(1)
