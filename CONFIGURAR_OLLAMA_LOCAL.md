# 🚀 Configurar Ollama Local com Túnel

Este guia explica como conectar o Ollama rodando no seu PC local ao CRM no servidor usando um túnel.

## 📋 Pré-requisitos

1. **Ollama instalado no seu PC**
   - Download: https://ollama.ai
   - Instale e baixe um modelo: `ollama pull llama3` (ou outro modelo)

2. **Ferramenta de túnel** (escolha uma):
   - **ngrok** (recomendado - mais fácil)
   - **Cloudflare Tunnel** (gratuito, sem limite)
   - **localtunnel** (gratuito, simples)

## 🔧 Opção 1: Usando ngrok (Recomendado)

### Passo 1: Instalar ngrok
- Windows: Baixe de https://ngrok.com/download
- Ou via chocolatey: `choco install ngrok`
- Ou via npm: `npm install -g ngrok`

### Passo 2: Criar conta e obter token
1. Crie conta gratuita em https://ngrok.com
2. Copie seu authtoken da dashboard
3. Configure: `ngrok config add-authtoken SEU_TOKEN`

### Passo 3: Iniciar túnel
```bash
ngrok http 11434
```

Isso vai gerar uma URL como: `https://abc123.ngrok-free.app`

### Passo 4: Configurar no CRM
1. Acesse o CRM como admin
2. Vá em "Configuração IA"
3. Crie nova configuração:
   - **Nome**: "Ollama Local (ngrok)"
   - **Provider**: `ollama`
   - **Model Name**: `llama3` (ou o modelo que você baixou)
   - **Base URL**: `https://abc123.ngrok-free.app` (URL do ngrok)
   - **API Key**: deixe vazio (Ollama não precisa)
   - Marque como **Ativo** e **Padrão**

### Passo 5: Testar
Use o botão "Testar Conexão" na configuração do CRM.

**⚠️ Importante**: A URL do ngrok muda a cada reinício (no plano gratuito). Você precisará atualizar a configuração no CRM quando reiniciar o ngrok.

**💡 Solução**: Use ngrok com domínio fixo (pago) ou Cloudflare Tunnel (gratuito com domínio fixo).

---

## 🔧 Opção 2: Usando Cloudflare Tunnel (Gratuito, Domínio Fixo)

### Passo 1: Instalar cloudflared
- Windows: Baixe de https://github.com/cloudflare/cloudflared/releases
- Ou via chocolatey: `choco install cloudflared`

### Passo 2: Criar túnel
```bash
cloudflared tunnel --url http://localhost:11434
```

Isso vai gerar uma URL como: `https://abc123.trycloudflare.com`

### Passo 3: Configurar no CRM
Mesmo processo da Opção 1, mas use a URL do Cloudflare.

**✅ Vantagem**: A URL permanece a mesma enquanto o túnel estiver ativo.

---

## 🔧 Opção 3: Usando localtunnel (Mais Simples)

### Passo 1: Instalar
```bash
npm install -g localtunnel
```

### Passo 2: Iniciar túnel
```bash
lt --port 11434
```

Isso vai gerar uma URL como: `https://abc123.loca.lt`

### Passo 3: Configurar no CRM
Mesmo processo, use a URL do localtunnel.

**⚠️ Limitação**: URLs mudam a cada reinício.

---

## 🔧 Opção 4: SSH Tunnel (Mais Seguro, Requer Acesso SSH)

Se você tem acesso SSH ao servidor:

### No seu PC (Windows):
```bash
ssh -R 11434:localhost:11434 usuario@servidor
```

### No servidor, configure no CRM:
- **Base URL**: `http://localhost:11434`

**✅ Vantagem**: Mais seguro, não expõe para internet.

---

## 📝 Configuração Recomendada no CRM

```
Nome: Ollama Local
Provider: ollama
Model Name: llama3 (ou llama3:70b, mistral, etc.)
Base URL: [URL do seu túnel]
API Key: (deixe vazio)
Ativo: ✅
Padrão: ✅
```

## 🧪 Modelos Recomendados para Ollama

- **llama3** - Bom equilíbrio velocidade/qualidade
- **llama3:70b** - Mais poderoso, mais lento
- **mistral** - Rápido e eficiente
- **mixtral** - Mais poderoso que mistral
- **neural-chat** - Otimizado para conversas

## ⚠️ Considerações

1. **Performance**: Ollama local pode ser mais lento que APIs cloud
2. **Recursos**: Modelos grandes precisam de RAM (llama3:70b precisa ~40GB)
3. **Latência**: Depende da sua conexão com o servidor
4. **Disponibilidade**: Seu PC precisa estar ligado e com túnel ativo

## 🔄 Manter Túnel Ativo

Para manter o túnel rodando em background no Windows:

### Com ngrok:
Crie um arquivo `start-ngrok.bat`:
```batch
@echo off
cd /d "C:\caminho\para\ngrok"
ngrok http 11434
pause
```

### Com Cloudflare:
```batch
@echo off
cloudflared tunnel --url http://localhost:11434
pause
```

Ou use um serviço Windows para iniciar automaticamente.

## 🐛 Troubleshooting

**Erro de conexão:**
- Verifique se o Ollama está rodando: `ollama list`
- Teste localmente: `curl http://localhost:11434/api/tags`
- Verifique se o túnel está ativo
- Verifique firewall do Windows

**Timeout:**
- Aumente o timeout no código (já está em 120s)
- Verifique sua conexão de internet

**Modelo não encontrado:**
- Baixe o modelo: `ollama pull llama3`
- Verifique o nome do modelo na configuração

