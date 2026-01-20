import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

/**
 * API Client - Usando Next.js API Routes
 *
 * Esta configuração usa as API Routes do Next.js que se conectam internamente
 * ao backend FastAPI via rede Docker, eliminando problemas de Mixed Content.
 */

// Criar instância do axios usando as API Routes locais do Next.js
const api: AxiosInstance = axios.create({
  baseURL: '', // API Routes locais (/api/*)
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor de requisição: adicionar token
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  // Adicionar token de autenticação
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }

  return config;
});

// Interceptor de resposta: tratar erros de autenticação
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
