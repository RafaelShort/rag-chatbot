import axios from "axios"
import type { ChatRequest, ChatResponse, CollectionInfo, DocumentInfo, HealthResponse, IngestResponse } from "../types"

const api = axios.create({
  baseURL: "/api",
  timeout: 120000,
})

export const ragApi = {
  health: async (): Promise<HealthResponse> => {
    const { data } = await api.get("/health")
    return data
  },

  collectionInfo: async (): Promise<CollectionInfo> => {
    const { data } = await api.get("/documents/collection/info")
    return data
  },

  listDocuments: async (): Promise<DocumentInfo[]> => {
    const { data } = await api.get("/documents")
    return data
  },

  ingestText: async (text: string, title: string): Promise<IngestResponse> => {
    const { data } = await api.post("/documents/ingest-text", { text, title }, { timeout: 120000 })
    return data
  },

  ingestFile: async (file: File, onProgress?: (pct: number) => void): Promise<IngestResponse> => {
    const form = new FormData()
    form.append("file", file)
    const { data } = await api.post("/documents/upload", form, {
      timeout: 180000,
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (e) => {
        if (onProgress && e.total) onProgress(Math.round((e.loaded * 100) / e.total))
      },
    })
    return data
  },

  chat: async (request: ChatRequest): Promise<ChatResponse> => {
    const { data } = await api.post("/chat", request, { timeout: 120000 })
    return data
  },

  deleteDocument: async (documentId: string): Promise<void> => {
    await api.delete("/documents/" + documentId)
  },
}
