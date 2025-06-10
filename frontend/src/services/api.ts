import axios, { AxiosRequestConfig, AxiosResponse } from 'axios';
import cacheService from './cache';

const API_BASE_URL = '/api/v1';

interface QueueItem {
  resolve: (value: any) => void;
  reject: (reason?: any) => void;
}

let isRefreshing = false;
let failedQueue: QueueItem[] = [];

const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  
  failedQueue = [];
};

const CACHE_ENABLED = true;
const DEFAULT_CACHE_TTL = 5 * 60 * 1000; // 5 минут
const CACHE_KEYS = {
  ANALYSES: 'analyses',
  ANALYSIS_BY_ID: (id: string) => `analysis_${id}`,
  ANALYSIS_RESULTS: (id: string) => `analysis_results_${id}`,
};

const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      const fixedToken = ensureValidTokenFormat(token);
      config.headers['Authorization'] = `Bearer ${fixedToken}`;
      
      if (fixedToken !== token) {
        localStorage.setItem('access_token', fixedToken);
      }
    }
    
    if (!(config.data instanceof FormData)) {
      config.headers['Content-Type'] = 'application/json';
    }
    
    return config;
  },
  (error) => Promise.reject(error)
);

function ensureValidTokenFormat(token: string): string {
  const parts = token.split('.');
  if (parts.length === 3) {
    return token;
  }
  
  return token;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response) {
      if (error.response.status === 401 && !originalRequest._retry) {
        const isAnalysisPage = window.location.pathname.startsWith('/analysis/result/');
        const isAnalysisHistoryPage = window.location.pathname.startsWith('/analysis/history');
        const isAnalysisAction = originalRequest.url.includes('/analyses');
        
        const isAuthRequest = originalRequest.url.includes('/auth/login') || 
                              originalRequest.url.includes('/auth/register') || 
                              originalRequest.url.includes('/auth/refresh');
        
        if (!isAuthRequest) {
          if (isRefreshing) {
            return new Promise((resolve, reject) => {
              failedQueue.push({ resolve, reject });
            })
              .then(token => {
                originalRequest.headers['Authorization'] = `Bearer ${token}`;
                return apiClient(originalRequest);
              })
              .catch(err => {
                return Promise.reject(err);
              });
          }
          
          originalRequest._retry = true;
          isRefreshing = true;
          
          try {
            const newToken = await authApi.refreshToken();
            
            originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
            processQueue(null, newToken);
            
            return apiClient(originalRequest);
          } catch (refreshError: any) {
            processQueue(refreshError as Error, null);
            
            if (isAnalysisPage || isAnalysisHistoryPage || isAnalysisAction) {
              window.dispatchEvent(new CustomEvent('sessionExpired', { 
                detail: { message: 'Сессия истекла. Пожалуйста, войдите снова.' }
              }));
              
              const authError = new Error('Сессия истекла. Пожалуйста, обновите страницу или выполните повторный вход.');
              authError.name = 'AuthSessionExpired';
              return Promise.reject(authError);
            } else if (window.location.pathname !== '/login') {
              localStorage.removeItem('access_token');
              localStorage.removeItem('refresh_token');
              localStorage.removeItem('user_data');
              
              window.location.href = '/login?session_expired=true';
            }
            
            return Promise.reject(refreshError);
          } finally {
            isRefreshing = false;
          }
        }
      }
    }
    
    return Promise.reject(error);
  }
);

const cachedGet = async <T>(url: string, config?: AxiosRequestConfig, cacheKey?: string, ttl: number = DEFAULT_CACHE_TTL): Promise<T> => {
  if (!CACHE_ENABLED || !cacheKey) {
    const response = await apiClient.get<T>(url, config);
    return response.data;
  }
  
  const currentToken = localStorage.getItem('access_token');
  
  const cachedData = cacheService.get<T>(cacheKey);
  const cachedToken = cacheService.get<string>(`${cacheKey}_token`);
  
  if (cachedData && cachedToken === currentToken) {
    return cachedData;
  }
  
  const response = await apiClient.get<T>(url, config);
  cacheService.set(cacheKey, response.data, ttl);
  if (currentToken) {
    cacheService.set(`${cacheKey}_token`, currentToken, ttl);
  }
  return response.data;
};

const isValidJWT = (token: string | null): boolean => {
  if (!token) return false;
  
  const parts = token.split('.');
  if (parts.length !== 3) {
    return false;
  }
  
  try {
    atob(parts[0]);
    atob(parts[1]);
    return true;
  } catch (e) {
    return false;
  }
};

export const userApi = {
  register: (userData: any) => {
    return apiClient.post('/auth/register', userData);
  },

  login: (email: string, password: string) => {
    return apiClient.post('/auth/login', { email, password });
  },

  forgotPassword: (email: string) => {
    return apiClient.post('/auth/forgot-password', { email });
  },

  resetPassword: (token: string, password: string) => {
    return apiClient.post('/auth/reset-password', { token, password });
  },

  getProfile: () => {
    return apiClient.get('/auth/me');
  },
  
  updateProfile: (userData: any) => {
    return apiClient.put('/auth/profile', userData);
  },
  
  changePassword: (passwordData: { currentPassword: string; newPassword: string }) => {
    return apiClient.post('/auth/change-password', passwordData);
  },
  
  updateAvatar: (formData: FormData) => {
    return apiClient.post('/auth/avatar', formData);
  },
};

export const analysisApi = {
  testToken: () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      return { valid: false, message: 'Токен отсутствует' };
    }
    
    const isValid = isValidJWT(token);
    
    const parts = token.split('.');
    
    if (parts.length === 3) {
      try {
        const header = JSON.parse(atob(parts[0]));
        const payload = JSON.parse(atob(parts[1]));
        return { 
          valid: isValid, 
          message: 'Токен в правильном формате JWT',
          header,
          payload
        };
      } catch (e) {
        return { valid: false, message: 'Ошибка декодирования токена' };
      }
    }
    
    return { 
      valid: isValid, 
      message: isValid ? 'Токен валиден' : 'Токен невалиден'
    };
  },

  createAnalysis: async (data: { marketplace: string; url: string; max_reviews: number }) => {
    const response = await apiClient.post('/analyses/', data);
    
    cacheService.remove(CACHE_KEYS.ANALYSES);
    return response;
  },

  testDirectBackendRequest: async () => {
    const token = localStorage.getItem('access_token');
    
    if (token) {
      const segments = token.split('.');
    }
    
    try {
      const directResponse = await axios.get('http://localhost:8000/api/v1/analyses/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Debug-Token': 'direct-backend-request'
        }
      });
      return directResponse.data;
    } catch (error: any) {
      return { error: 'Ошибка прямого запроса' };
    }
  },

  getAllAnalyses: async () => {
    const token = localStorage.getItem('access_token');
    
    if (token) {
      const segments = token.split('.');
    }
    
    const debugMode = false; 
    if (debugMode) {
        const directResponse = await axios.get('/api/v1/analyses/', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'X-Debug-Token': 'analyses-request',
                'Content-Type': 'application/json'
            }
        });
        return directResponse.data;
    }
    
    try {
      const headers = {
        'Authorization': `Bearer ${token}`,
        'X-Debug-Token': 'analyses-request',
        'Content-Type': 'application/json'
      };
      
      const response = await apiClient.get('/analyses/', {
        headers: headers
      });
      return response.data;
    } catch (error: any) {
      if (error.response && error.response.status === 401) {
      }
      throw error;
    }
  },

  getAnalysisById: async (id: string) => {
    const response = await apiClient.get(`/analyses/${id}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    return response.data;
  },

  getAnalysisResults: async (id: string) => {
    const response = await apiClient.get(`/analyses/${id}/results`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    return response.data;
  },

  deleteAnalysis: async (id: string) => {
    const response = await apiClient.delete(`/analyses/${id}`);
    cacheService.remove(CACHE_KEYS.ANALYSES);
    cacheService.remove(CACHE_KEYS.ANALYSIS_BY_ID(id));
    cacheService.remove(CACHE_KEYS.ANALYSIS_RESULTS(id));
    return response;
  },

  saveCompletedAnalysis: async (
    analysisId: string, 
    resultsData: {
      positive_aspects: any[]; 
      negative_aspects: any[]; 
      aspect_categories: any;    
      reviews_count: number;
      sentiment_summary: any;   
    }
  ) => {
    const payload = {
      request_id: parseInt(analysisId, 10), 
      ...resultsData
    };
    const response = await apiClient.post('/analysis/save_analysis', payload); 
    cacheService.remove(CACHE_KEYS.ANALYSES);
    cacheService.remove(CACHE_KEYS.ANALYSIS_BY_ID(analysisId));
    return response.data; 
  },

  exportAnalysisResults: async (id: string) => {
    return apiClient.get(`/analyses/${id}/export`, {
      responseType: 'blob',
    });
  },
  
  sendReportByEmail: async (id: string, email: string, format: string) => {
    return apiClient.post(`/analyses/${id}/send-report`, { email, format });
  },

  performLiveAnalysis: async (data: { marketplace: string; url: string; max_reviews: number }) => {
    const response = await apiClient.post('/analysis/analyze_reviews', data);
    return response.data; 
  },
};

export const authApi = {
  register: (data: { email: string; password: string; username: string }) => {
    return apiClient.post('/auth/register', data);
  },

  login: (data: { email: string; password: string }) => {
    return apiClient.post('/auth/login', data);
  },

  logout: () => {
    cacheService.clear();
    return apiClient.post('/auth/logout');
  },

  getCurrentUser: () => {
    return apiClient.get('/auth/me');
  },
  
  refreshToken: async (): Promise<string> => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }
      
      const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
        refresh_token: refreshToken
      });
      
      if (response.data && response.data.access_token) {
        const newToken = response.data.access_token;
        
        localStorage.setItem('access_token', newToken);
        
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
        
        return newToken;
      } else {
        throw new Error('Failed to refresh token');
      }
    } catch (error: any) {
      if (error && error.response && error.response.status === 401) { 
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_data'); 
      }
      throw error;
    }
  }
};

export default apiClient;