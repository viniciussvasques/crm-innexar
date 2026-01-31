
import requests
import json
import uuid

BASE_URL = "http://localhost:8000/api/ai/public/chat"
SESSION_ID = str(uuid.uuid4())

def send_message(message):
    payload = {
        "message": message,
        "session_id": SESSION_ID,
        "language": "pt"
    }
    
    try:
        response = requests.post(BASE_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        print(f"\nUser: {message}")
        print(f"Helena: {data.get('response')}")
        return data
    except Exception as e:
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Details: {e.response.text}")

print(f"Starting Tool Verification Session: {SESSION_ID}")

# 1. Ask about status (Helena should know about the tool)
send_message("Como posso ver o status do meu pedido?")

# 2. Try to trigger the tool
send_message("Verificar status do email cliente@exemplo.com")
