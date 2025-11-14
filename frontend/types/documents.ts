export enum DocumentStatus {
  UPLOADED = 'uploaded',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

export enum DocumentType {
  UNKNOWN = 'unknown',
  INVOICE = 'invoice',
  CONTRACT = 'contract',
  RESUME = 'resume',
  RECEIPT = 'receipt',
  FORM = 'form',
  LETTER = 'letter',
  REPORT = 'report',
  OTHER = 'other'
}

export interface Document {
  id: number
  filename: string
  original_filename: string
  file_size: number
  file_type: string
  storage_path: string
  status: DocumentStatus
  extracted_text?: string
  page_count?: number
  extraction_method?: string
  extraction_error?: string
  task_id?: string
  retry_count: number
  processing_time?: number
  document_type: DocumentType
  document_type_confidence?: number
  extracted_data?: Record<string, any>
  summary?: string
  ai_processing_cost?: number
  created_at: string
  updated_at: string
}

export interface DocumentListResponse {
  total: number
  items: Document[]
  page: number
  page_size: number
}

export interface SearchResult {
  id: number
  filename: string
  original_filename: string
  document_type: string
  status: string
  summary?: string
  created_at: string
  score?: number
}

export interface SearchResponse {
  query: string
  total: number
  results: SearchResult[]
  search_type: string
  page: number
  page_size: number
}

export interface WebSocketMessage {
  type: string
  document_id?: number
  status?: string
  message?: string
  progress?: number
  metadata?: Record<string, any>
  timestamp?: number
}