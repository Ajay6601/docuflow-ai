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
  extracted_text?: string | null
  page_count?: number | null
  extraction_method?: string | null
  extraction_error?: string | null
  task_id?: string | null
  retry_count: number
  processing_time?: number | null
  document_type: DocumentType
  document_type_confidence?: number | null
  extracted_data?: Record<string, any> | null
  summary?: string | null
  ai_processing_cost?: number | null
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
  summary?: string | null
  created_at: string
  score?: number | null
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
  connection_id?: string
}