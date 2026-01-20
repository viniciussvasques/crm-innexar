#!/usr/bin/env python3
"""
Script para testar todos os endpoints da API Innexar CRM
"""
import requests
import json
import sys
from typing import Dict, Optional

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg: str):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")

def test_endpoint(
    method: str,
    endpoint: str,
    token: Optional[str] = None,
    data: Optional[Dict] = None,
    expected_status: int = 200,
    description: str = ""
) -> bool:
    """Testa um endpoint e retorna True se sucesso"""
    url = f"{API_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            print_error(f"Método {method} não suportado")
            return False
        
        status_ok = response.status_code == expected_status
        
        if status_ok:
            print_success(f"{method} {endpoint} ({response.status_code})")
            if description:
                print_info(f"  → {description}")
            return True
        elif response.status_code in [401, 403]:
            print_warning(f"{method} {endpoint} - Auth Required ({response.status_code})")
            return False
        else:
            print_error(f"{method} {endpoint} - FAIL ({response.status_code})")
            try:
                error_data = response.json()
                print_error(f"  Erro: {json.dumps(error_data, indent=2)[:200]}")
            except:
                print_error(f"  Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print_error(f"{method} {endpoint} - TIMEOUT")
        return False
    except requests.exceptions.ConnectionError:
        print_error(f"{method} {endpoint} - CONNECTION ERROR")
        return False
    except Exception as e:
        print_error(f"{method} {endpoint} - ERROR: {str(e)}")
        return False

def main():
    print(f"\n{'='*60}")
    print(f"🧪 Testando Endpoints da API Innexar CRM")
    print(f"{'='*60}")
    print(f"Base URL: {BASE_URL}\n")
    
    # 1. Health Check
    print("1️⃣  Health Check")
    test_endpoint("GET", "/", description="Verifica se API está rodando")
    print()
    
    # 2. Login
    print("2️⃣  Autenticação")
    print_info("Fazendo login como admin@innexar.app...")
    login_data = {
        "email": "admin@innexar.app",
        "password": "admin123"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            token_data = response.json()
            TOKEN = token_data.get("access_token")
            print_success(f"Login OK - Token obtido")
            print()
        else:
            print_error(f"Login FAIL ({response.status_code})")
            print_error(f"Response: {response.text[:200]}")
            print_warning("Continuando testes sem autenticação...")
            TOKEN = None
            print()
    except Exception as e:
        print_error(f"Erro no login: {str(e)}")
        TOKEN = None
        print()
    
    # 3. Usuários
    if TOKEN:
        print("3️⃣  Usuários")
        test_endpoint("GET", "/users/me", TOKEN, description="Obter usuário atual")
        test_endpoint("GET", "/users/", TOKEN, description="Listar usuários (admin)")
        print()
    
    # 4. Contatos
    if TOKEN:
        print("4️⃣  Contatos")
        test_endpoint("GET", "/contacts/", TOKEN, description="Listar contatos")
        print()
    
    # 5. Oportunidades
    if TOKEN:
        print("5️⃣  Oportunidades")
        test_endpoint("GET", "/opportunities/", TOKEN, description="Listar oportunidades")
        print()
    
    # 6. Projetos
    if TOKEN:
        print("6️⃣  Projetos")
        test_endpoint("GET", "/projects", TOKEN, description="Listar projetos")
        print()
    
    # 7. Atividades
    if TOKEN:
        print("7️⃣  Atividades")
        test_endpoint("GET", "/activities/", TOKEN, description="Listar atividades")
        print()
    
    # 8. Dashboard
    if TOKEN:
        print("8️⃣  Dashboard")
        test_endpoint("GET", "/dashboard/admin", TOKEN, description="Dashboard admin")
        test_endpoint("GET", "/dashboard/vendedor", TOKEN, description="Dashboard vendedor")
        print()
    
    # 9. Comissões
    if TOKEN:
        print("9️⃣  Comissões")
        test_endpoint("GET", "/commissions/", TOKEN, description="Listar comissões")
        print()
    
    # 10. Metas
    if TOKEN:
        print("🔟 Metas")
        test_endpoint("GET", "/goals/", TOKEN, description="Listar metas")
        print()
    
    # 11. Notificações
    if TOKEN:
        print("1️⃣1️⃣  Notificações")
        test_endpoint("GET", "/notifications/", TOKEN, description="Listar notificações")
        print()
    
    # 12. Templates
    if TOKEN:
        print("1️⃣2️⃣  Templates")
        test_endpoint("GET", "/templates/", TOKEN, description="Listar templates")
        print()
    
    # 13. Quote Requests
    if TOKEN:
        print("1️⃣3️⃣  Quote Requests")
        test_endpoint("GET", "/quote-requests/", TOKEN, description="Listar solicitações de orçamento")
        print()
    
    # 14. AI
    if TOKEN:
        print("1️⃣4️⃣  IA")
        test_endpoint(
            "POST",
            "/ai/chat",
            TOKEN,
            {"prompt": "teste", "max_tokens": 100},
            description="Chat com IA"
        )
        print()
    
    print(f"{'='*60}")
    print("✅ Testes concluídos!")
    print(f"{'='*60}\n")
    print("Para testar com outro servidor:")
    print(f"  python3 test_all_endpoints.py http://api.sales.innexar.app\n")

if __name__ == "__main__":
    main()

