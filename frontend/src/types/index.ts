export interface Source {
  content: string
  score: number
  document_id: string
  chunk_index: number
  rerank_score: number | null
}

export interface ChatResponse {
  answer: string
  sources: Source[]
  query: string
  total_sources_found: number
}

export interface ChatRequest {
  query: string
  document_id?: string
  top_k?: number
  use_reranker?: boolean
}

export interface IngestResponse {
  document_id: string
  filename: string
  chunks_indexed: number
  total_chars: number
  strategy: string
}

export interface DocumentInfo {
  document_id: string
  filename: string
  file_type: string
  chunks_count: number
}

export interface CollectionInfo {
  name: string
  vectors_count: number
  points_count: number
  status: string
}

export interface HealthResponse {
  status: string
  provider: string
  model: string
  qdrant_url: string
  qdrant_status: string
  collection_info: CollectionInfo
}

export interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  sources?: Source[]
  timestamp: Date
  isLoading?: boolean
}
