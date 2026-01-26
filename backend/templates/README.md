# Sistema de Templates

## Estrutura

```
templates/
├── landing-page/
│   ├── base/              # Estrutura base do template
│   ├── variants/          # Variantes de estilo
│   └── prompts/           # Prompts de customização
└── README.md
```

## Como Funciona

1. **Template Base**: Estrutura completa de arquivos Next.js
2. **Variantes**: Configurações de estilo (cores, layout)
3. **Customização IA**: Apenas conteúdo e ajustes finos

## Economia de Tokens

- **Sem Template**: ~50k tokens (gerar tudo)
- **Com Template**: ~10k tokens (apenas customização)
- **Economia**: ~80%
