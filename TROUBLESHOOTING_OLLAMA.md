# 🔧 Troubleshooting - Ollama com Túnel

## ❌ Erro ao acessar túnel Cloudflare

### Passo 1: Verificar se Ollama está rodando

No PowerShell, teste localmente:

```powershell
# Teste se o Ollama responde localmente
curl http://localhost:11434/api/tags
```

**Se der erro:**
1. Verifique se o Ollama está instalado:
   ```powershell
   ollama --version
   ```

2. Se não estiver instalado, baixe de: https://ollama.ai/download

3. Baixe um modelo:
   ```powershell
   ollama pull llama3.1
   ```

4. Verifique se o serviço está rodando:
   ```powershell
   # Ollama geralmente inicia automaticamente
   # Se não, tente:
   ollama serve
   ```

### Passo 2: Verificar Firewall

O firewall do Windows pode estar bloqueando:

```powershell
# Teste se a porta está acessível
Test-NetConnection -ComputerName localhost -Port 11434
```

**Se estiver bloqueado:**
1. Abra o Firewall do Windows
2. Permita conexões na porta 11434
3. Ou desative temporariamente para teste

### Passo 3: Verificar Túnel Cloudflare

1. **O túnel ainda está rodando?**
   - Verifique se o PowerShell com `cloudflared tunnel` ainda está aberto
   - Se fechou, rode novamente:
     ```powershell
     cloudflared tunnel --url http://localhost:11434
     ```
   - **Atenção**: A URL pode mudar a cada execução!

2. **Teste a URL do túnel:**
   ```powershell
   curl https://become-particles-affair-listed.trycloudflare.com/api/tags
   ```

3. **Se der erro 502 ou timeout:**
   - O túnel pode não estar conseguindo conectar ao localhost
   - Tente usar `127.0.0.1` em vez de `localhost`:
     ```powershell
     cloudflared tunnel --url http://127.0.0.1:11434
     ```

### Passo 4: Alternativa - Usar ngrok

Se o Cloudflare não funcionar, tente ngrok (mais simples):

1. **Instalar ngrok:**
   - Download: https://ngrok.com/download
   - Ou: `choco install ngrok`

2. **Criar conta gratuita:**
   - https://ngrok.com
   - Copie o authtoken

3. **Configurar:**
   ```powershell
   ngrok config add-authtoken SEU_TOKEN
   ```

4. **Iniciar túnel:**
   ```powershell
   ngrok http 11434
   ```

5. **Use a URL gerada** (ex: `https://abc123.ngrok-free.app`)

### Passo 5: Verificar no CRM

Quando configurar no CRM:

1. **Base URL deve ser:**
   - Cloudflare: `https://become-particles-affair-listed.trycloudflare.com`
   - ngrok: `https://abc123.ngrok-free.app`
   - **SEM barra no final!**

2. **Model Name:**
   - Use exatamente o nome do modelo que você baixou
   - Exemplos: `llama3.1`, `llama3`, `mistral`, `neural-chat`

3. **Teste a conexão:**
   - Use o botão "Testar Conexão" no CRM
   - Se der erro, verifique os logs

## 🔍 Erros Comuns

### Erro: "Connection refused"
- **Causa**: Ollama não está rodando
- **Solução**: Inicie o Ollama ou baixe um modelo

### Erro: "502 Bad Gateway"
- **Causa**: Túnel não consegue conectar ao localhost
- **Solução**: Use `127.0.0.1` em vez de `localhost`

### Erro: "Timeout"
- **Causa**: Firewall bloqueando ou conexão lenta
- **Solução**: Verifique firewall e conexão de internet

### Erro: "Model not found"
- **Causa**: Nome do modelo incorreto
- **Solução**: Liste modelos: `ollama list` e use o nome exato

## ✅ Checklist de Verificação

- [ ] Ollama instalado e rodando
- [ ] Modelo baixado (`ollama pull modelo`)
- [ ] Teste local funciona: `curl http://localhost:11434/api/tags`
- [ ] Firewall permite porta 11434
- [ ] Túnel Cloudflare/ngrok rodando
- [ ] URL do túnel testada e funcionando
- [ ] Base URL no CRM está correta (sem barra no final)
- [ ] Model Name no CRM está correto

## 🆘 Ainda com problemas?

1. **Verifique logs do Ollama:**
   ```powershell
   # Ollama geralmente mostra logs no terminal
   # Se não, verifique eventos do Windows
   ```

2. **Teste com curl direto:**
   ```powershell
   # Teste local
   curl http://localhost:11434/api/generate -d '{"model":"llama3.1","prompt":"teste"}'
   
   # Teste pelo túnel (substitua pela sua URL)
   curl https://SUA-URL/api/generate -d '{"model":"llama3.1","prompt":"teste"}'
   ```

3. **Verifique se o modelo existe:**
   ```powershell
   ollama list
   ```

