import { Language } from '@/types'
import ptTranslations from './i18n/pt'
import enTranslations from './i18n/en'
import esTranslations from './i18n/es'

export type TranslationKey = string

// Mapear traduções importadas
const translations = {
  pt: ptTranslations,
  en: enTranslations,
  es: esTranslations
}

// Função síncrona para obter tradução (mais confiável)
export function getTranslation(language: Language, key: string, params?: Record<string, string>): string {
  try {
    const keys = key.split('.')
    let value: any = translations[language]

    // Se não encontrar no idioma solicitado, tenta português
    if (!value && language !== 'pt') {
      value = translations.pt
    }

    // Se ainda não encontrou, usa português como fallback
    if (!value) {
      value = translations.pt
    }

    for (const k of keys) {
      value = value?.[k]
      if (value === undefined) break
    }

    // Se encontrou o valor, substitui variáveis se necessário
    if (typeof value === 'string') {
      if (params) {
        let result = value
        for (const [paramKey, paramValue] of Object.entries(params)) {
          result = result.replace(new RegExp(`\\{${paramKey}\\}`, 'g'), paramValue)
        }
        return result
      }
      return value
    }

    // Se não encontrou, tenta fallback para português
    if (language !== 'pt') {
      value = translations.pt
      for (const k of keys) {
        value = value?.[k]
        if (value === undefined) break
      }
      if (typeof value === 'string') {
        if (params) {
          let result = value
          for (const [paramKey, paramValue] of Object.entries(params)) {
            result = result.replace(new RegExp(`\\{${paramKey}\\}`, 'g'), paramValue)
          }
          return result
        }
        return value
      }
    }

    // Fallback final: retorna a última chave ou a chave completa
    return key.split('.').pop() || key
  } catch (error) {
    console.error('Erro ao traduzir:', key, error)
    // Fallback final
    return key.split('.').pop() || key
  }
}

// Função assíncrona para compatibilidade (retorna diretamente)
export async function getTranslations(language: Language): Promise<any> {
  return translations[language] || translations.pt
}

// Hook para usar traduções (compatibilidade com código existente)
export function useTranslations() {
  return {
    t: (key: string) => key,
    language: 'pt' as Language
  }
}