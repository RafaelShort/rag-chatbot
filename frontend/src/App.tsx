import { useState } from "react"
import { ChatWindow } from "./components/chat/ChatWindow"
import { UploadPanel } from "./components/upload/UploadPanel"
import { DocumentList } from "./components/documents/DocumentList"

export default function App() {
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  const handleIngestSuccess = () => {
    setRefreshTrigger((prev) => prev + 1)
  }

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100">
      <aside className="w-80 shrink-0 border-r border-gray-800 bg-gray-900 flex flex-col overflow-hidden">
        <div className="px-4 py-4 border-b border-gray-800">
          <h1 className="text-lg font-bold text-blue-400">RAG System</h1>
          <p className="text-xs text-gray-500">Ollama + Qdrant + LangChain</p>
        </div>
        <div className="flex-1 overflow-y-auto flex flex-col">
          <UploadPanel onSuccess={handleIngestSuccess} />
          <div className="border-t border-gray-800 px-4 pt-4 pb-6">
            <DocumentList refreshTrigger={refreshTrigger} />
          </div>
        </div>
      </aside>
      <main className="flex-1 flex flex-col overflow-hidden">
        <ChatWindow />
      </main>
    </div>
  )
}
