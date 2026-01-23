# Site Spec Schema - AI Site Generator

## Visão Geral

O `site_spec.json` é o contrato central que define todas as características do site a ser gerado. Ele é criado a partir do onboarding e usado por todas as etapas do pipeline.

---

## Schema JSON (TypeScript Types)

```typescript
interface SiteSpec {
  version: string;  // "1.0"
  project_id: string;
  created_at: string;  // ISO 8601
  
  business: BusinessInfo;
  design: DesignSpec;
  pages: PageSpec[];
  seo: SEOSpec;
  integrations: IntegrationsSpec;
}

interface BusinessInfo {
  name: string;
  tagline?: string;
  industry: string;
  description: string;
  target_audience: string;
  value_proposition: string;
  differentiators: string[];
  services?: Service[];
  contact: ContactInfo;
}

interface Service {
  name: string;
  description: string;
  icon?: string;
}

interface ContactInfo {
  email: string;
  phone?: string;
  address?: string;
  social?: {
    facebook?: string;
    instagram?: string;
    linkedin?: string;
    twitter?: string;
  };
}

interface DesignSpec {
  template_id: string;
  colors: {
    primary: string;      // hex
    secondary: string;    // hex
    accent: string;       // hex
    background: string;   // hex
    text: string;         // hex
  };
  fonts: {
    heading: string;      // Google Fonts name
    body: string;
  };
  tone: "professional" | "friendly" | "bold" | "minimal" | "creative";
  logo: {
    url: string;
    alt: string;
  };
}

interface PageSpec {
  slug: string;           // "home", "about", "services"
  title: string;
  meta_description: string;
  sections: SectionSpec[];
}

interface SectionSpec {
  type: string;           // "hero", "features", "testimonials", etc
  variant?: string;       // Variante do componente
  content: Record<string, any>;  // Conteúdo específico da seção
  order: number;
}

interface SEOSpec {
  site_title: string;
  default_description: string;
  keywords: string[];
  og_image?: string;
  favicon?: string;
}

interface IntegrationsSpec {
  analytics?: {
    google_analytics_id?: string;
    gtm_id?: string;
  };
  forms?: {
    provider: "native" | "typeform" | "google_forms";
    config?: Record<string, any>;
  };
  chat?: {
    provider: "tawk" | "intercom" | "crisp" | "none";
    config?: Record<string, any>;
  };
}
```

---

## Exemplo Completo

```json
{
  "version": "1.0",
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-01-23T10:00:00Z",
  
  "business": {
    "name": "Dhv Group",
    "tagline": "Soluções que transformam seu negócio",
    "industry": "Consultoria Empresarial",
    "description": "A Dhv Group é uma empresa de consultoria especializada em transformação digital e otimização de processos para pequenas e médias empresas.",
    "target_audience": "PMEs que buscam modernização e eficiência operacional",
    "value_proposition": "Ajudamos empresas a crescer de forma sustentável através de processos otimizados e tecnologia de ponta",
    "differentiators": [
      "Atendimento personalizado",
      "Metodologia própria comprovada",
      "Resultados mensuráveis em 90 dias"
    ],
    "services": [
      {
        "name": "Consultoria Estratégica",
        "description": "Análise e planejamento estratégico para seu negócio",
        "icon": "strategy"
      },
      {
        "name": "Transformação Digital",
        "description": "Implementação de soluções tecnológicas modernas",
        "icon": "digital"
      },
      {
        "name": "Treinamento Corporativo",
        "description": "Capacitação de equipes para alta performance",
        "icon": "training"
      }
    ],
    "contact": {
      "email": "contato@dhvgroup.com",
      "phone": "+1 (555) 123-4567",
      "address": "123 Business Ave, Suite 100, New York, NY",
      "social": {
        "linkedin": "https://linkedin.com/company/dhvgroup",
        "instagram": "https://instagram.com/dhvgroup"
      }
    }
  },
  
  "design": {
    "template_id": "landing",
    "colors": {
      "primary": "#2563EB",
      "secondary": "#1E40AF",
      "accent": "#F59E0B",
      "background": "#0F172A",
      "text": "#F8FAFC"
    },
    "fonts": {
      "heading": "Inter",
      "body": "Inter"
    },
    "tone": "professional",
    "logo": {
      "url": "https://assets.innexar.app/projects/xxx/logo.png",
      "alt": "Dhv Group Logo"
    }
  },
  
  "pages": [
    {
      "slug": "home",
      "title": "Dhv Group | Soluções que transformam seu negócio",
      "meta_description": "Consultoria empresarial especializada em transformação digital e otimização de processos para PMEs.",
      "sections": [
        {
          "type": "hero",
          "variant": "centered",
          "order": 1,
          "content": {
            "headline": "Soluções que transformam seu negócio",
            "subheadline": "Ajudamos empresas a crescer de forma sustentável através de processos otimizados e tecnologia de ponta",
            "cta_primary": {
              "text": "Fale Conosco",
              "url": "#contact"
            },
            "cta_secondary": {
              "text": "Conheça nossos serviços",
              "url": "#services"
            },
            "background_image": null
          }
        },
        {
          "type": "features",
          "variant": "grid-3",
          "order": 2,
          "content": {
            "title": "Por que escolher a Dhv Group?",
            "subtitle": "Nossos diferenciais",
            "items": [
              {
                "icon": "users",
                "title": "Atendimento Personalizado",
                "description": "Cada cliente recebe atenção dedicada e soluções sob medida"
              },
              {
                "icon": "chart",
                "title": "Resultados Mensuráveis",
                "description": "Métricas claras e acompanhamento contínuo do progresso"
              },
              {
                "icon": "award",
                "title": "Metodologia Comprovada",
                "description": "Processos testados e refinados ao longo de anos de experiência"
              }
            ]
          }
        },
        {
          "type": "services",
          "variant": "cards",
          "order": 3,
          "content": {
            "title": "Nossos Serviços",
            "subtitle": "Como podemos ajudar seu negócio",
            "items": [
              {
                "icon": "strategy",
                "title": "Consultoria Estratégica",
                "description": "Análise e planejamento estratégico para seu negócio",
                "link": "/services#consultoria"
              },
              {
                "icon": "digital",
                "title": "Transformação Digital",
                "description": "Implementação de soluções tecnológicas modernas",
                "link": "/services#digital"
              },
              {
                "icon": "training",
                "title": "Treinamento Corporativo",
                "description": "Capacitação de equipes para alta performance",
                "link": "/services#training"
              }
            ]
          }
        },
        {
          "type": "testimonials",
          "variant": "carousel",
          "order": 4,
          "content": {
            "title": "O que nossos clientes dizem",
            "items": [
              {
                "quote": "A Dhv Group transformou nossa operação. Em 6 meses, reduzimos custos em 30% e aumentamos a produtividade.",
                "author": "Maria Silva",
                "role": "CEO",
                "company": "TechCorp",
                "avatar": null
              }
            ]
          }
        },
        {
          "type": "cta",
          "variant": "full-width",
          "order": 5,
          "content": {
            "title": "Pronto para transformar seu negócio?",
            "subtitle": "Entre em contato e descubra como podemos ajudar",
            "cta": {
              "text": "Agende uma Consultoria Gratuita",
              "url": "#contact"
            }
          }
        },
        {
          "type": "contact",
          "variant": "form-with-info",
          "order": 6,
          "content": {
            "title": "Entre em Contato",
            "subtitle": "Estamos prontos para ouvir você",
            "form_fields": ["name", "email", "phone", "message"],
            "show_contact_info": true,
            "show_social": true
          }
        }
      ]
    }
  ],
  
  "seo": {
    "site_title": "Dhv Group | Consultoria Empresarial",
    "default_description": "Consultoria empresarial especializada em transformação digital e otimização de processos para PMEs.",
    "keywords": [
      "consultoria empresarial",
      "transformação digital",
      "otimização de processos",
      "consultoria PME"
    ],
    "og_image": "https://assets.innexar.app/projects/xxx/og-image.png",
    "favicon": "https://assets.innexar.app/projects/xxx/favicon.png"
  },
  
  "integrations": {
    "analytics": {
      "google_analytics_id": null,
      "gtm_id": null
    },
    "forms": {
      "provider": "native",
      "config": {
        "recipient_email": "contato@dhvgroup.com"
      }
    },
    "chat": {
      "provider": "none"
    }
  }
}
```

---

## Tipos de Seções

| Tipo | Descrição | Variantes |
|------|-----------|-----------|
| `hero` | Seção principal | centered, left-aligned, with-image |
| `features` | Lista de features/benefícios | grid-3, grid-4, list |
| `services` | Serviços oferecidos | cards, list, tabs |
| `about` | Sobre a empresa | with-image, timeline |
| `testimonials` | Depoimentos | carousel, grid |
| `team` | Equipe | grid, carousel |
| `pricing` | Preços/planos | cards-3, comparison |
| `faq` | Perguntas frequentes | accordion, grid |
| `cta` | Call to action | full-width, centered |
| `contact` | Formulário de contato | form-only, form-with-info |
| `gallery` | Galeria de imagens | grid, masonry |
| `stats` | Estatísticas/números | inline, cards |
| `logos` | Logos de clientes | carousel, grid |
| `blog` | Preview de blog posts | grid, list |

---

## Validação

### JSON Schema para Validação

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["version", "project_id", "business", "design", "pages", "seo"],
  "properties": {
    "version": {"type": "string", "enum": ["1.0"]},
    "project_id": {"type": "string", "format": "uuid"},
    "business": {
      "type": "object",
      "required": ["name", "industry", "description", "target_audience", "contact"],
      "properties": {
        "name": {"type": "string", "minLength": 1, "maxLength": 100}
      }
    },
    "design": {
      "type": "object",
      "required": ["template_id", "colors", "fonts", "tone"],
      "properties": {
        "colors": {
          "type": "object",
          "required": ["primary", "secondary", "background", "text"],
          "properties": {
            "primary": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"}
          }
        }
      }
    },
    "pages": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["slug", "title", "sections"]
      }
    }
  }
}
```

---

## Transformação: Onboarding → Site Spec

```python
def onboarding_to_site_spec(onboarding: dict, project_id: str) -> SiteSpec:
    """Transforma dados de onboarding em site_spec"""
    
    # Mapear cores do tema
    color_themes = {
        "blue": {"primary": "#2563EB", "secondary": "#1E40AF"},
        "green": {"primary": "#059669", "secondary": "#047857"},
        "purple": {"primary": "#7C3AED", "secondary": "#5B21B6"},
        "red": {"primary": "#DC2626", "secondary": "#B91C1C"},
    }
    
    colors = color_themes.get(onboarding.get("color_preference", "blue"))
    
    return {
        "version": "1.0",
        "project_id": project_id,
        "created_at": datetime.now().isoformat(),
        "business": {
            "name": onboarding["business_name"],
            "industry": onboarding["industry"],
            "description": onboarding["description"],
            # ... processar outros campos
        },
        "design": {
            "template_id": onboarding.get("template", "landing"),
            "colors": colors,
            # ...
        },
        "pages": generate_pages(onboarding),
        "seo": generate_seo(onboarding),
        "integrations": {}
    }
```

---

*Última atualização: Janeiro 2026*
