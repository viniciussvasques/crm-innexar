# Estratégia de Personalização de Templates

## Visão Geral

Os templates são personalizados em **3 camadas**:

1. **Substituição de Placeholders** (Automático, sem IA)
2. **Geração de Conteúdo via IA** (Textos criativos)
3. **Ajustes Finais** (Opcional, via IA)

---

## Camada 1: Placeholders Estáticos

### Como Funciona
Substituição direta de strings nos arquivos do template.

### Placeholders Disponíveis

#### Informações Básicas
- `{{BUSINESS_NAME}}` - Nome do negócio
- `{{BUSINESS_DESCRIPTION}}` - Descrição do site
- `{{BUSINESS_TAGLINE}}` - Tagline/slogan
- `{{BUSINESS_EMAIL}}` - Email de contato
- `{{BUSINESS_PHONE}}` - Telefone
- `{{BUSINESS_ADDRESS}}` - Endereço completo

#### Cores
- `{{PRIMARY_COLOR}}` - Cor primária (ex: #3B82F6)
- `{{SECONDARY_COLOR}}` - Cor secundária
- `{{ACCENT_COLOR}}` - Cor de destaque
- `{{PRIMARY_COLOR_DARK}}` - Versão escura da primária (calculada automaticamente)
- `{{SECONDARY_COLOR_DARK}}` - Versão escura da secundária

#### Conteúdo
- `{{HERO_TITLE}}` - Título do hero (padrão: "Bem-vindo à {{BUSINESS_NAME}}")
- `{{HERO_SUBTITLE}}` - Subtítulo do hero
- `{{CTA_TEXT}}` - Texto do botão principal
- `{{ABOUT_PREVIEW_TEXT}}` - Texto resumido sobre
- `{{ABOUT_FULL_TEXT}}` - Texto completo sobre
- `{{YEARS_IN_BUSINESS}}` - Anos de experiência

#### Redes Sociais
- `{{SOCIAL_FACEBOOK}}` - URL do Facebook
- `{{SOCIAL_INSTAGRAM}}` - URL do Instagram

#### Horários
- `{{BUSINESS_HOURS}}` - Horários formatados (ex: "Segunda-feira: 9h-18h\n...")

### Blocos Condicionais

#### Serviços
```tsx
{{#SERVICES}}
  { title: 'Serviço 1', description: 'Descrição...' },
  { title: 'Serviço 2', description: 'Descrição...' },
{{/SERVICES}}
```
- Se `onboarding.services` estiver vazio, o bloco inteiro é removido
- Se houver serviços, gera lista formatada

#### Depoimentos
```tsx
{{#TESTIMONIALS}}
  { name: 'Cliente', text: 'Depoimento...', rating: 5 },
{{/TESTIMONIALS}}
```
- Se não houver depoimentos, usa depoimentos padrão
- Se houver, usa os reais

---

## Camada 2: Geração de Conteúdo via IA

### Quando é Usado
Após substituir placeholders, a IA gera conteúdo mais criativo e personalizado.

### O que a IA Gera

```json
{
  "hero_title": "Título criativo e envolvente (max 60 chars)",
  "hero_subtitle": "Subtítulo persuasivo (max 120 chars)",
  "about_preview": "Resumo sobre o negócio (2-3 frases)",
  "about_full": "Texto completo sobre (4-6 frases)",
  "service_descriptions": {
    "Serviço 1": "Descrição profissional e atrativa (2-3 frases)",
    "Serviço 2": "Descrição profissional e atrativa (2-3 frases)"
  }
}
```

### Como é Aplicado
1. IA recebe dados do onboarding (nome, nicho, serviços, tom)
2. IA gera JSON com conteúdo personalizado
3. Sistema substitui textos genéricos pelos gerados
4. Arquivos são atualizados

### Vantagens
- **Economia de tokens**: ~10k tokens (vs ~50k gerando tudo)
- **Qualidade**: Templates garantem estrutura, IA personaliza conteúdo
- **Consistência**: Todos os sites têm estrutura profissional

---

## Camada 3: Ajustes Finais (Opcional)

### Quando Usar
Para customizações mais complexas que não cabem em placeholders.

### Exemplos
- Ajustar layout baseado em número de serviços
- Adicionar seções específicas do nicho
- Modificar componentes baseado em preferências

### Implementação Futura
Pode ser expandido conforme necessário.

---

## Fluxo Completo de Personalização

```
1. Selecionar Template
   └─ Baseado em: niche, tone, selected_pages

2. Copiar Template Base
   └─ Copia todos os arquivos para target_dir

3. Substituir Placeholders
   └─ Loop em todos os arquivos (.tsx, .ts, .js, .json, .css)
   └─ Substitui {{PLACEHOLDER}} por valores reais
   └─ Remove blocos condicionais vazios

4. Gerar Conteúdo via IA
   └─ Chama IA com dados do onboarding
   └─ Recebe JSON com textos personalizados
   └─ Atualiza arquivos com conteúdo gerado

5. Validação
   └─ Verifica se arquivos essenciais existem
   └─ Valida estrutura Next.js

6. Pronto para Deploy
   └─ Site estático completo e personalizado
```

---

## Como Criar um Novo Template

### Estrutura Obrigatória

```
template-name/
└── base/
    ├── package.json          # Dependências Next.js
    ├── tsconfig.json         # Config TypeScript
    ├── next.config.js        # Config Next.js (output: 'export')
    ├── tailwind.config.js    # Config Tailwind (com {{PRIMARY_COLOR}})
    ├── postcss.config.js     # Config PostCSS
    ├── .gitignore            # Git ignore
    ├── README.md             # Documentação
    ├── app/
    │   ├── layout.tsx        # Layout raiz (com {{BUSINESS_NAME}})
    │   ├── page.tsx          # Home page
    │   ├── globals.css       # Estilos globais (com {{PRIMARY_COLOR}})
    │   └── [outras-páginas]/
    ├── components/           # Componentes reutilizáveis
    └── lib/                  # Utilitários
```

### Placeholders Obrigatórios

Todo template DEVE usar:
- `{{BUSINESS_NAME}}` - No mínimo no Header/Footer
- `{{PRIMARY_COLOR}}` - No tailwind.config.js e globals.css
- `{{BUSINESS_EMAIL}}` e `{{BUSINESS_PHONE}}` - No Footer/Contato
- `{{HERO_TITLE}}` e `{{HERO_SUBTITLE}}` - Na home page
- `{{#SERVICES}}...{{/SERVICES}}` - Se tiver seção de serviços

### Boas Práticas

1. **Responsivo**: Mobile-first, Tailwind CSS
2. **Acessível**: Semântico HTML, ARIA labels
3. **Performance**: Imagens otimizadas, lazy loading
4. **SEO**: Meta tags, structured data
5. **Moderno**: Next.js 14 App Router, TypeScript
6. **Estático**: `output: 'export'` no next.config.js

---

## Seleção de Template

### Lógica Atual
```python
def select_template(onboarding: SiteOnboarding) -> str:
    # Por enquanto, sempre retorna "premium-static"
    return "premium-static"
```

### Lógica Futura (Recomendada)
```python
def select_template(onboarding: SiteOnboarding) -> str:
    niche = onboarding.niche
    
    template_map = {
        SiteNiche.RESTAURANT: "restaurant",
        SiteNiche.LAWYER: "professional-services",
        SiteNiche.DENTIST: "professional-services",
        SiteNiche.REAL_ESTATE: "real-estate",
        SiteNiche.GENERAL: "premium-static",
        # ... outros nichos
    }
    
    tone = onboarding.tone
    if tone == SiteTone.PREMIUM:
        return f"{template_map.get(niche, 'premium-static')}-premium"
    
    return template_map.get(niche, "premium-static")
```

---

## Exemplo de Uso no Template

### app/page.tsx
```tsx
import Hero from '@/components/Hero'

export default function Home() {
  return (
    <>
      <Hero 
        title="{{HERO_TITLE}}"
        subtitle="{{HERO_SUBTITLE}}"
      />
      {{#SERVICES}}
      <ServicesSection services={[
        {{#SERVICES}}
      ]} />
      {{/SERVICES}}
    </>
  )
}
```

### tailwind.config.js
```js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: '{{PRIMARY_COLOR}}',
        secondary: '{{SECONDARY_COLOR}}',
      }
    }
  }
}
```

### components/Footer.tsx
```tsx
export default function Footer() {
  return (
    <footer>
      <p>{{BUSINESS_NAME}}</p>
      <p>Email: {{BUSINESS_EMAIL}}</p>
      <p>Tel: {{BUSINESS_PHONE}}</p>
      {{#SOCIAL_FACEBOOK}}
      <a href="{{SOCIAL_FACEBOOK}}">Facebook</a>
      {{/SOCIAL_FACEBOOK}}
    </footer>
  )
}
```

---

## Resumo

✅ **Placeholders**: Substituição automática de dados básicos
✅ **IA**: Geração de conteúdo criativo e personalizado
✅ **Templates**: Estrutura profissional garantida
✅ **Economia**: ~80% menos tokens vs gerar tudo do zero
✅ **Qualidade**: Sites consistentes e profissionais
