# Implementação de Templates - Plano Profissional

## Status Atual

✅ **Estrutura Criada**: `backend/templates/` e `TemplateService`
✅ **Endpoint de Status**: Criado e funcionando
✅ **Arquitetura Documentada**: `ARQUITETURA_PROFISSIONAL.md`

## Próximos Passos

### 1. Criar Templates Base

Criar templates reais em `backend/templates/`:

```
templates/
├── landing-page/
│   ├── base/
│   │   ├── app/
│   │   │   ├── page.tsx          # Template com placeholders
│   │   │   ├── layout.tsx
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   ├── Header.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── Hero.tsx
│   │   └── package.json
│   └── variants/
│       ├── saas.json
│       └── ecommerce.json
```

### 2. Modificar SiteGeneratorService

Integrar `TemplateService` no fluxo de geração:

```python
# Em generate_site():
1. Selecionar template baseado em niche
2. Copiar template base para target_dir
3. Gerar prompt de customização (muito menor)
4. Chamar IA apenas para customização
5. Aplicar customizações ao template
```

### 3. Reduzir Prompt da IA

**Antes** (gerar tudo):
- ~50k tokens
- Prompt completo com toda estrutura

**Depois** (customizar template):
- ~10k tokens
- Prompt apenas com dados do cliente
- IA retorna apenas customizações

### 4. Testar e Validar

1. Criar template base funcional
2. Testar geração com template
3. Validar economia de tokens
4. Validar qualidade do resultado

## Benefícios

1. **Economia de Tokens**: ~80% de redução
2. **Geração Mais Rápida**: Menos tokens = resposta mais rápida
3. **Resultado Mais Consistente**: Template garante estrutura correta
4. **Manutenção Mais Fácil**: Templates podem ser atualizados independentemente

## Decisão de Implementação

**Opção A**: Implementar templates agora (recomendado)
- Economiza tokens imediatamente
- Melhora qualidade
- Reduz custos

**Opção B**: Manter geração completa por enquanto
- Funciona, mas consome muitos tokens
- Pode ser melhorado depois

## Recomendação

**Implementar templates gradualmente**:
1. Criar 1 template base (landing-page) funcional
2. Testar com 1-2 gerações
3. Se funcionar bem, expandir para outros templates
4. Manter fallback para geração completa se template não existir
