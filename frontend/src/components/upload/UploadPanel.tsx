import { useState, useCallback } from "react"
import { useDropzone } from "react-dropzone"
import { ragApi } from "../../api/client"
import { Button } from "../ui/Button"
import { IngestResponse } from "../../types"

interface UploadPanelProps {
  onSuccess?: () => void
}

const MIN_TEXT_LENGTH = 10

export function UploadPanel({ onSuccess }: UploadPanelProps) {
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [lastResult, setLastResult] = useState<IngestResponse | null>(null)
  const [error, setError] = useState("")
  const [textMode, setTextMode] = useState(false)
  const [textTitle, setTextTitle] = useState("")
  const [textContent, setTextContent] = useState("")

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (!acceptedFiles.length) return
      setUploading(true)
      setError("")
      setProgress(0)
      setLastResult(null)
      try {
        const result = await ragApi.ingestFile(acceptedFiles[0], setProgress)
        setLastResult(result)
        onSuccess?.()
      } catch {
        setError("Erro ao fazer upload do arquivo.")
      } finally {
        setUploading(false)
        setProgress(0)
      }
    },
    [onSuccess]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "text/plain": [".txt"],
      "text/markdown": [".md"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    },
    maxFiles: 1,
    disabled: uploading,
  })

  const textTooShort = textContent.trim().length > 0 && textContent.trim().length < MIN_TEXT_LENGTH
  const canSubmit = textTitle.trim().length > 0 && textContent.trim().length >= MIN_TEXT_LENGTH

  const handleTextIngest = async () => {
    if (!canSubmit) return
    setUploading(true)
    setError("")
    setLastResult(null)
    try {
      const result = await ragApi.ingestText(textContent, textTitle)
      setLastResult(result)
      setTextTitle("")
      setTextContent("")
      onSuccess?.()
    } catch {
      setError("Erro ao indexar texto.")
    } finally {
      setUploading(false)
    }
  }

  const dropClasses = [
    "border-2 border-dashed rounded-xl p-6 text-center transition-colors",
    uploading ? "opacity-50 cursor-not-allowed" : "cursor-pointer",
    isDragActive
      ? "border-blue-500 bg-blue-500/10"
      : "border-gray-700 hover:border-gray-500",
  ].join(" ")

  return (
    <div className="p-4 flex flex-col gap-4">
      <div>
        <h2 className="font-semibold text-gray-100 mb-1">Upload</h2>
        <p className="text-xs text-gray-500">PDF, DOCX, TXT ou Markdown</p>
      </div>

      <div className="flex gap-2">
        <Button
          size="sm"
          variant={!textMode ? "primary" : "secondary"}
          onClick={() => setTextMode(false)}
        >
          Arquivo
        </Button>
        <Button
          size="sm"
          variant={textMode ? "primary" : "secondary"}
          onClick={() => setTextMode(true)}
        >
          Texto
        </Button>
      </div>

      {!textMode && (
        <div {...getRootProps()} className={dropClasses}>
          <input {...getInputProps()} />
          <div className="text-3xl mb-2">📄</div>
          {isDragActive ? (
            <p className="text-blue-400 text-sm">Solte aqui...</p>
          ) : (
            <p className="text-gray-400 text-sm">
              Arraste ou <span className="text-blue-400">clique</span>
            </p>
          )}
          {uploading && (
            <div className="mt-3">
              <div className="w-full bg-gray-700 rounded-full h-1.5">
                <div
                  className="bg-blue-500 h-1.5 rounded-full transition-all"
                  style={{ width: progress + "%" }}
                />
              </div>
              <p className="text-xs text-gray-400 mt-1">{progress}%</p>
            </div>
          )}
        </div>
      )}

      {textMode && (
        <div className="flex flex-col gap-3">
          <input
            type="text"
            value={textTitle}
            onChange={(e) => setTextTitle(e.target.value)}
            placeholder="Titulo do documento"
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
          <div className="flex flex-col gap-1">
            <textarea
              value={textContent}
              onChange={(e) => setTextContent(e.target.value)}
              placeholder="Cole o conteudo aqui... (minimo 10 caracteres)"
              rows={5}
              className={[
                "bg-gray-800 border rounded-lg px-3 py-2 text-sm text-gray-100 placeholder-gray-500 resize-none focus:outline-none transition-colors",
                textTooShort
                  ? "border-yellow-500 focus:border-yellow-400"
                  : "border-gray-700 focus:border-blue-500",
              ].join(" ")}
            />
            <div className="flex justify-between items-center px-1">
              {textTooShort ? (
                <p className="text-yellow-500 text-xs">
                  Minimo {MIN_TEXT_LENGTH} caracteres ({textContent.trim().length}/{MIN_TEXT_LENGTH})
                </p>
              ) : (
                <span />
              )}
              <p className="text-xs text-gray-600 ml-auto">
                {textContent.trim().length} chars
              </p>
            </div>
          </div>
          <Button
            onClick={handleTextIngest}
            loading={uploading}
            disabled={!canSubmit}
          >
            Indexar Texto
          </Button>
        </div>
      )}

      {error && (
        <p className="text-red-400 text-xs bg-red-400/10 rounded-lg px-3 py-2">
          {error}
        </p>
      )}

      {lastResult && (
        <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3">
          <p className="text-green-400 text-xs font-medium">
            Indexado com sucesso!
          </p>
          <p className="text-xs text-gray-400 mt-0.5">
            {lastResult.chunks_indexed} chunks · {lastResult.total_chars} chars
          </p>
        </div>
      )}
    </div>
  )
}
