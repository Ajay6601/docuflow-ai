import axios from 'axios'
import type { Document, DocumentListResponse, SearchResponse } from '../types/document'

const API_BASE_URL = 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

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
    const params: Record<string, any> = { page, page_size: pageSize }
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
    window.URL.revokeObjectURL(url)
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

export default api