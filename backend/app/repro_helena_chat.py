
import asyncio
import httpx
import uuid
import json

BASE_URL = "http://localhost:8000"

async def test_chat_flow():
    session_id = str(uuid.uuid4())
    print(f"Starting chat session: {session_id}")
    
    # 1. First message
    msg1 = "quero fazer um aplicativo para minha mecanica"
    print(f"\nUser: {msg1}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/ai/public/chat",
            json={
                "message": msg1,
                "session_id": session_id,
                "language": "pt"
            }
        )
        
        if response.status_code != 200:
            print(f"Error: {response.text}")
            return
            
        data = response.json()
        print(f"Helena: {data.get('response')}")
        
    # 2. Second message
    msg2 = "quero com agendamento e cadastro de clientes"
    print(f"\nUser: {msg2}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/ai/public/chat",
            json={
                "message": msg2,
                "session_id": session_id,
                "language": "pt"
            }
        )
        
        if response.status_code != 200:
            print(f"Error: {response.text}")
            return
            
        data = response.json()
        print(f"Helena: {data.get('response')}")

if __name__ == "__main__":
    asyncio.run(test_chat_flow())
