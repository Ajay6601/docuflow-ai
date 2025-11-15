import axios from 'axios'
import { Document, DocumentListResponse, SearchResponse } from '../types/document'

const API_BASE_URL = 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 responses (unauthorized)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  // Register new user
  register: async (email: string, username: string, password: string, fullName?: string) => {
    const response = await api.post('/auth/register', {
      email,
      username,
      password,
      full_name: fullName,
    })
    return response.data
  },

  // Login - UPDATED to use JSON endpoint
  login: async (username: string, password: string) => {
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)

    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
    return response.data
  },

  // Get current user
  getCurrentUser: async () => {
    const response = await api.get('/auth/me')
    return response.data
  },

  // Logout
   logout: async () => {
    const response = await api.post('/auth/logout')
    return response.data
  },
}

export const documentApi = {
  // Upload document
  upload: async (file: File, processAsync: boolean = true): Promise<Document> => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('process_async', String(processAsync))
    
    const response = await api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // List documents
  list: async (page: number = 1, pageSize: number = 10, statusFilter?: string): Promise<DocumentListResponse> => {
    const params: any = { page, page_size: pageSize }
    if (statusFilter) params.status_filter = statusFilter
    
    const response = await api.get('/documents/', { params })
    return response.data
  },

  // Get single document
  get: async (id: number): Promise<Document> => {
    const response = await api.get(`/documents/${id}`)
    return response.data
  },

  // Delete document
  delete: async (id: number): Promise<void> => {
    await api.delete(`/documents/${id}`)
  },

  // Reprocess document
  reprocess: async (id: number): Promise<Document> => {
    const response = await api.post(`/documents/${id}/process`)
    return response.data
  },

  // Get document status
  getStatus: async (id: number): Promise<any> => {
    const response = await api.get(`/documents/${id}/status`)
    return response.data
  },

  // Download document
  download: async (id: number, filename: string): Promise<void> => {
    const response = await api.get(`/documents/${id}/download`, {
      responseType: 'blob',
    })
    
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
  },
}

export const searchApi = {
  // Full-text search
  fullText: async (query: string, page: number = 1, pageSize: number = 10): Promise<SearchResponse> => {
    const response = await api.get('/search/full-text', {
      params: { q: query, page, page_size: pageSize }
    })
    return response.data
  },

  // Semantic search
  semantic: async (query: string, page: number = 1, pageSize: number = 10): Promise<SearchResponse> => {
    const response = await api.get('/search/semantic', {
      params: { q: query, page, page_size: pageSize }
    })
    return response.data
  },

  // Hybrid search
  hybrid: async (query: string, page: number = 1, pageSize: number = 10): Promise<SearchResponse> => {
    const response = await api.get('/search/hybrid', {
      params: { q: query, page, page_size: pageSize }
    })
    return response.data
  },
}

export const analyticsApi = {
  // Get overview statistics
  getOverview: async () => {
    const response = await api.get('/analytics/overview')
    return response.data
  },

  // Get document types distribution
  getDocumentTypes: async () => {
    const response = await api.get('/analytics/document-types')
    return response.data
  },

  // Get upload timeline
  getUploadTimeline: async (days: number = 7) => {
    const response = await api.get('/analytics/upload-timeline', {
      params: { days }
    })
    return response.data
  },

  // Get processing stats
  getProcessingStats: async (days: number = 7) => {
    const response = await api.get('/analytics/processing-stats', {
      params: { days }
    })
    return response.data
  },

  // Get cost tracking
  getCostTracking: async (days: number = 30) => {
    const response = await api.get('/analytics/cost-tracking', {
      params: { days }
    })
    return response.data
  },

  // Get extraction methods
  getExtractionMethods: async () => {
    const response = await api.get('/analytics/extraction-methods')
    return response.data
  },

  // Get recent activity
  getRecentActivity: async (limit: number = 10) => {
    const response = await api.get('/analytics/recent-activity', {
      params: { limit }
    })
    return response.data
  },
}

export default api