# Templates de Sites Estáticos

Coleção de templates profissionais e responsivos para geração automática de sites.

## Templates Disponíveis

### 1. `premium-static` ✅
**Nicho**: Geral, negócios diversos
**Características**: 
- Design premium e elegante
- Seções: Hero, Serviços, Sobre, Depoimentos, CTA
- Ideal para: Empresas em geral, prestadores de serviço

### 2. `modern-landing` ✅
**Nicho**: Landing pages, conversão
**Características**:
- Foco em conversão
- Seções: Hero impactante, Features, Benefits, CTA
- Ideal para: Campanhas, produtos, serviços com foco em conversão

### 3. `professional-services` 🚧
**Nicho**: Advogados, dentistas, consultores
**Características**:
- Design profissional e confiável
- Destaque para contato telefônico
- Seções: Hero, Serviços, Por que escolher, CTA
- Ideal para: Profissionais liberais, serviços especializados

### 4. `ecommerce-minimal` 🚧
**Nicho**: Lojas online, e-commerce
**Características**:
- Design minimalista e focado em produtos
- Grid de produtos
- Ideal para: Lojas virtuais, catálogos

### 5. `portfolio-creative` 🚧
**Nicho**: Portfólios, criativos, designers
**Características**:
- Design criativo e visual
- Galeria de trabalhos
- Ideal para: Designers, fotógrafos, artistas

## Estrutura

Cada template segue a estrutura:

```
template-name/
└── base/
    ├── package.json
    ├── tsconfig.json
    ├── next.config.js
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── .gitignore
    ├── README.md
    ├── app/
    │   ├── layout.tsx
    │   ├── page.tsx
    │   ├── globals.css
    │   └── [páginas]/
    ├── components/
    └── lib/
```

## Placeholders

Todos os templates usam placeholders que são substituídos automaticamente:

- `{{BUSINESS_NAME}}` - Nome do negócio
- `{{PRIMARY_COLOR}}` - Cor primária
- `{{HERO_TITLE}}` - Título do hero
- `{{#SERVICES}}...{{/SERVICES}}` - Lista de serviços
- E muitos outros (ver ESTRATEGIA_PERSONALIZACAO.md)

## Como Usar

O `TemplateService` seleciona automaticamente o template baseado em:
- `onboarding.niche` - Nicho do negócio
- `onboarding.tone` - Tom (professional, friendly, premium)

## Personalização

1. **Placeholders**: Substituição automática de dados
2. **IA**: Geração de conteúdo criativo (hero, descrições)
3. **Templates**: Estrutura profissional garantida

Ver `ESTRATEGIA_PERSONALIZACAO.md` para detalhes completos.
