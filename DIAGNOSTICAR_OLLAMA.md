# 🔍 Diagnosticar Problemas com Ollama

## ❌ Modelo "ola" não conecta

### Passo 1: Verificar se o modelo existe no Ollama

No PowerShell, execute:

```powershell
ollama list
```

**Verifique:**
- O modelo "ola" aparece na lista?
- O nome está escrito exatamente como aparece? (pode ser "ola", "Ola", "OLA", etc.)

**Se o modelo NÃO aparecer:**
```powershell
# Baixe o modelo
ollama pull ola

# Ou verifique se o nome está correto
ollama list
```

### Passo 2: Testar o modelo localmente

```powershell
# Teste se o modelo funciona localmente
ollama run ola
```

Se funcionar localmente, o problema é na conexão com o servidor.

### Passo 3: Verificar se o túnel está ativo

**Cloudflare:**
- Verifique se o PowerShell com `cloudflared tunnel` ainda está aberto
- A URL pode ter mudado se você reiniciou o túnel

**Teste a URL do túnel:**
```powershell
# Substitua pela sua URL atual
curl https://SUA-URL.trycloudflare.com/api/tags
```

Se retornar JSON com os modelos, o túnel está funcionando.

### Passo 4: Verificar configuração no CRM

No CRM, verifique:

1. **Base URL:**
   - Deve ser a URL completa do túnel (ex: `https://become-particles-affair-listed.trycloudflare.com`)
   - **SEM barra no final!**
   - **SEM `http://` ou `https://` duplicado**

2. **Model Name:**
   - Deve ser exatamente o nome que aparece em `ollama list`
   - **Case-sensitive!** (ola ≠ Ola ≠ OLA)
   - Sem espaços extras

3. **Provider:**
   - Deve ser `ollama`

4. **Status:**
   - Deve estar marcado como **Ativo** e **Padrão**

### Passo 5: Testar conexão no CRM

1. Clique em "Testar Conexão" na configuração
2. Veja a mensagem de erro (agora mais detalhada)

**Erros comuns e soluções:**

- **"Modelo 'ola' não encontrado"**
  - O modelo não está instalado ou o nome está errado
  - Solução: `ollama pull ola` ou corrija o nome

- **"Não foi possível conectar ao Ollama"**
  - Túnel não está ativo ou URL errada
  - Solução: Verifique se o túnel está rodando e use a URL correta

- **"Timeout"**
  - Conexão lenta ou modelo muito pesado
  - Solução: Aguarde ou use um modelo menor

### Passo 6: Verificar logs do backend

```bash
docker logs crm-backend --tail 50 | grep -i ollama
```

Isso mostra erros detalhados do backend.

## ✅ Checklist de Verificação

- [ ] Modelo "ola" existe em `ollama list`
- [ ] Modelo funciona localmente: `ollama run ola`
- [ ] Túnel Cloudflare/ngrok está rodando
- [ ] URL do túnel está correta no CRM (sem barra no final)
- [ ] Nome do modelo no CRM está exatamente igual ao `ollama list`
- [ ] Configuração está marcada como Ativo e Padrão
- [ ] Teste de conexão no CRM mostra erro específico

## 🆘 Ainda não funciona?

1. **Tente outro modelo:**
   ```powershell
   ollama pull llama3.1
   ```
   Use `llama3.1` no CRM

2. **Verifique se o Ollama está rodando:**
   ```powershell
   curl http://localhost:11434/api/tags
   ```

3. **Reinicie o túnel:**
   - Feche o túnel atual
   - Rode novamente: `cloudflared tunnel --url http://localhost:11434`
   - Use a nova URL no CRM

4. **Teste direto pelo túnel:**
   ```powershell
   curl https://SUA-URL/api/generate -d '{"model":"ola","prompt":"teste","stream":false}'
   ```


