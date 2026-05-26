import { useCallback, useEffect, useState } from "react"
import { ragApi } from "../../api/client"
import { DocumentInfo } from "../../types"

interface DocumentListProps {
  refreshTrigger: number
}

const FILE_ICONS: Record<string, string> = {
  ".pdf": "📄",
  ".txt": "📝",
  ".md": "📝",
  ".docx": "📋",
  ".doc": "📋",
  text: "📝",
}

export function DocumentList({ refreshTrigger }: DocumentListProps) {
  const [documents, setDocuments] = useState<DocumentInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [error, setError] = useState("")

  const fetchDocuments = useCallback(async () => {
    setLoading(true)
    setError("")
    try {
      const docs = await ragApi.listDocuments()
      setDocuments(docs)
    } catch {
      setError("Erro ao listar documentos.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchDocuments()
  }, [fetchDocuments, refreshTrigger])

  const handleDelete = async (documentId: string, filename: string) => {
    if (!window.confirm(`Deletar "${filename}"?`)) return
    setDeletingId(documentId)
    setError("")
    try {
      await ragApi.deleteDocument(documentId)
      setDocuments((prev) => prev.filter((d) => d.document_id !== documentId))
    } catch {
      setError("Erro ao deletar documento.")
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">
          Indexados ({documents.length})
        </p>
        <button
          onClick={fetchDocuments}
          disabled={loading}
          className="text-gray-500 hover:text-gray-300 transition-colors disabled:opacity-40 text-sm"
          title="Atualizar lista"
        >
          {loading ? "⏳" : "🔄"}
        </button>
      </div>

      {error && (
        <p className="text-red-400 text-xs bg-red-400/10 rounded-lg px-3 py-2">{error}</p>
      )}

      {!loading && documents.length === 0 && (
        <p className="text-xs text-gray-600 text-center py-6">
          Nenhum documento indexado ainda
        </p>
      )}

      <div className="flex flex-col gap-2">
        {documents.map((doc) => (
          <div
            key={doc.document_id}
            className="bg-gray-800 border border-gray-700 rounded-lg p-3 flex items-start gap-2 group"
          >
            <span className="text-base shrink-0 mt-0.5">
              {FILE_ICONS[doc.file_type] ?? "📁"}
            </span>
            <div className="flex-1 min-w-0">
              <p
                className="text-sm text-gray-100 font-medium truncate"
                title={doc.filename}
              >
                {doc.filename}
              </p>
              <p className="text-xs text-gray-500 mt-0.5">
                {doc.chunks_count} chunks · {doc.file_type}
              </p>
            </div>
            <button
              onClick={() => handleDelete(doc.document_id, doc.filename)}
              disabled={deletingId === doc.document_id}
              className="shrink-0 text-gray-600 hover:text-red-400 transition-colors disabled:opacity-40 opacity-0 group-hover:opacity-100"
              title="Deletar documento"
            >
              {deletingId === doc.document_id ? "⏳" : "🗑️"}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
