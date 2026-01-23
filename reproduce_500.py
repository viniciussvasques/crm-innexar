import sys
import os
import asyncio
from fastapi.testclient import TestClient

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.main import app

client = TestClient(app)

def test_endpoint():
    print("Testing /health...")
    try:
        response = client.get("/health")
        print(f"Health Status: {response.status_code}")
        print(response.json())
    except Exception as e:
        print(f"Health check crashed: {e}")

    print("\nTesting /api/system-config (expecting auth error or 500)...")
    try:
        # We don't have a token, so it should return 401 Not Authenticated
        # If it returns 500, it means the *dependency itself* crashed before checking auth
        response = client.get("/api/system-config/")
        print(f"Status: {response.status_code}")
        if response.status_code == 500:
             print("CRITICAL: Returned 500 Internal Server Error")
             print(response.text)
        else:
             print(f"Response: {response.text}")
    except Exception as e:
        print(f"Request crashed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_endpoint()
