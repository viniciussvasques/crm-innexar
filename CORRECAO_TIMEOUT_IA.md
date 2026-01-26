# 🔧 Correção: Timeout na Geração de IA

## ❌ Problema Identificado

**Sintoma:**
- Order 24 estava processando
- IA chamada mas falhando com `httpx.ReadTimeout`
- Status revertido para `BUILDING` após erro
- Nenhum arquivo gerado

**Causa Raiz:**
1. **Timeout muito curto**: 120 segundos não é suficiente para geração de código completo
2. **Status revertido**: Quando falha, status volta para `BUILDING` impedindo retry automático
3. **Erro vazio**: Mensagem de erro não estava sendo capturada corretamente

## ✅ Correções Aplicadas

### 1. **Timeout Aumentado**
- ✅ Timeout aumentado de 120s para **300s (5 minutos)**
- ✅ Suficiente para geração de código completo
- ✅ Aplicado apenas para Cloudflare (geração de código)

### 2. **Tratamento de Erro Melhorado**
- ✅ Captura específica de `httpx.ReadTimeout`
- ✅ Mensagens de erro mais descritivas
- ✅ Captura de `HTTPStatusError` para erros HTTP

### 3. **Status Não Reverte Mais**
- ✅ Quando falha, status permanece `GENERATING`
- ✅ Permite retry automático via `auto-start-stuck-orders`
- ✅ Sistema pode detectar e retentar automaticamente

## 📋 Mudanças Técnicas

**`ai_service.py` - `_call_cloudflare`:**
```python
# Antes: timeout=120.0
# Depois: timeout=300.0 (5 minutos)

# Adicionado tratamento específico:
except httpx.ReadTimeout:
    raise ValueError("Cloudflare API timeout after 300 seconds...")
except httpx.HTTPStatusError as e:
    raise ValueError(f"Cloudflare API error {e.response.status_code}...")
```

**`site_generator_service.py` - Tratamento de erro:**
```python
# Antes: order.status = SiteOrderStatus.BUILDING
# Depois: Mantém GENERATING para permitir retry automático
```

## 🎯 Resultado Esperado

- ✅ Geração de código tem 5 minutos para completar
- ✅ Se falhar, status permanece GENERATING
- ✅ Sistema pode retentar automaticamente
- ✅ Mensagens de erro mais claras

## 📊 Status Atual

- ✅ Order 24 reiniciado com timeout aumentado
- ✅ Código corrigido e aplicado
- ✅ Worker reiniciado

**A geração deve funcionar agora com o timeout maior!**
