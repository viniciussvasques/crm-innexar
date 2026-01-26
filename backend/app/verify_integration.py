import asyncio
import httpx
import uuid
import time
import sys

BASE_URL = "http://localhost:8000/api"

async def run_verification():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 0: Login
        print("=== Step 0: Admin Login ===")
        try:
            resp = await client.post(f"{BASE_URL}/auth/login", json={
                "email": "admin@innexar.app",
                "password": "admin123"
            })
            resp.raise_for_status()
            token = resp.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print(f"✅ Logged in! Token obtained.")
        except Exception as e:
            print(f"❌ Failed to login: {e}")
            if hasattr(e, 'response'):
                print(e.response.text)
            return

        print("\n=== Step 1: Create Order (Simulate Stripe Webhook) ===")
        session_id = f"sess_{uuid.uuid4()}"
        print(f"Generated Session ID: {session_id}")
        
        order_payload = {
            "customer_name": "Test User",
            "customer_email": "test@innexar.com",
            "customer_phone": "+5511999999999",
            "stripe_session_id": session_id,
            "total_price": 297.00,
            "addon_ids": []
        }
        
        try:
            # Create order does not require auth (public webhook usually, but here checking endpoint)
            # The endpoint `create_order` at `POST /` does NOT have `require_admin` in `site_orders.py` line 276
            resp = await client.post(f"{BASE_URL}/site-orders/", json=order_payload)
            resp.raise_for_status()
            order = resp.json()
            order_id = order["id"]
            print(f"✅ Order Created! ID: {order_id}, Status: {order['status']}")
        except Exception as e:
            print(f"❌ Failed to create order: {e}")
            if hasattr(e, 'response'):
                print(e.response.text)
            # Try with auth if it failed? No, webhook should be public.
            return

        print("\n=== Step 2: Submit Onboarding (Simulate Website Form) ===")
        # Wait a bit
        await asyncio.sleep(1)
        
        onboarding_payload = {
            "business_name": "TechStart Solutions",
            "business_email": "contact@techstart.com",
            "business_phone": "+5511999999999",
            "has_whatsapp": True,
            "business_address": "Av Paulista, 1000",
            
            "niche": "other",
            "custom_niche": "technology",
            "primary_city": "São Paulo",
            "state": "SP",
            "service_areas": ["Brasil"],
            
            "services": ["Software Development", "Cloud Migration", "IT Consulting"],
            "primary_service": "Software Development",
            
            "site_objective": "Generate leads and showcase portfolio",
            "site_description": "We are a modern tech consultancy focused on digital transformation.",
            "selected_pages": ["Home", "About", "Services", "Contact"],
            "total_pages": 4,
            "tone": "professional",
            "primary_cta": "call",
            "cta_text": "Agendar Consultoria",
            
            "primary_color": "#0F172A",
            "secondary_color": "#3B82F6",
            "accent_color": "#10B981",
            
            "is_complete": True,
            "completed_steps": 7,
            "password": "InitialPassword123!" # For account creation
        }
        
        try:
            # Note: Endpoint uses session_id as identifier in path
            resp = await client.post(f"{BASE_URL}/site-orders/{session_id}/onboarding", json=onboarding_payload)
            resp.raise_for_status()
            result = resp.json()
            print(f"✅ Onboarding Submitted! Response: {result}")
            print(f"   Note: Generation Started: {result.get('generation_started')}")
        except Exception as e:
            print(f"❌ Failed to submit onboarding: {e}")
            if hasattr(e, 'response'):
                print(e.response.text)
            return

        print("\n=== Step 3: Monitor Generation (Simulate Client Portal) ===")
        print("Polling logs every 2 seconds...")
        
        start_time = time.time()
        phase1_detected = False
        
        while time.time() - start_time < 60: # Max 60s wait
            try:
                # Check Status (Protected)
                resp_order = await client.get(f"{BASE_URL}/site-orders/{order_id}", headers=headers)
                resp_order.raise_for_status()
                order_data = resp_order.json()
                status = order_data["status"]
                
                # Check Deliverables
                deliverables = order_data.get("deliverables", [])
                
                # Check Logs (Protected)
                resp_logs = await client.get(f"{BASE_URL}/site-orders/{order_id}/logs", headers=headers)
                logs = []
                if resp_logs.status_code == 200:
                    logs = resp_logs.json()
                
                # Print latest log
                if logs:
                    latest = logs[-1]
                    print(f"[{status}] Log: {latest['message']}")
                    
                    if "Strategy" in latest["message"] or "Briefing" in latest["message"]:
                        phase1_detected = True
                
                if deliverables:
                    print(f"🎉 Deliverables Found: {len(deliverables)}")
                    for d in deliverables:
                        print(f"   - {d['type'].upper()}: {d['title']} ({d['status']})")
                        if d['type'] == 'briefing' and (d['status'] == 'ready' or d['status'] == 'approved'):
                            print("\n✅ SUCCESS: Briefing generated!")
                            return

                await asyncio.sleep(2)
            except Exception as e:
                print(f"Error polling: {e}")
                await asyncio.sleep(2)
        
        print("\n⚠️ Timeout waiting for generation completion.")

if __name__ == "__main__":
    asyncio.run(run_verification())
