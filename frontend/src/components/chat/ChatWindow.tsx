import { useEffect, useRef, useState } from "react"
import { Message } from "../../types"
import { ragApi } from "../../api/client"
import { ChatMessage } from "./ChatMessage"
import { ChatInput } from "./ChatInput"

export function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "0",
      role: "assistant",
      content: "Ola! Sou seu assistente RAG. Faca upload de documentos e me faca perguntas sobre eles.",
      timestamp: new Date(),
    },
  ])
  const [loading, setLoading] = useState(false)
  const [topK, setTopK] = useState(5)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSend = async (text: string) => {
    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text,
      timestamp: new Date(),
    }
    const loadingMsg: Message = {
      id: "loading",
      role: "assistant",
      content: "",
      timestamp: new Date(),
      isLoading: true,
    }
    setMessages((prev) => [...prev, userMsg, loadingMsg])
    setLoading(true)

    try {
      const response = await ragApi.chat({ query: text, top_k: topK })
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.answer,
        sources: response.sources,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev.filter((m) => m.id !== "loading"), aiMsg])
    } catch {
      const errMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Erro ao processar sua pergunta. Verifique se o backend esta rodando.",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev.filter((m) => m.id !== "loading"), errMsg])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b border-gray-800 bg-gray-900 flex items-center justify-between">
        <div>
          <h2 className="font-semibold text-gray-100">Chat RAG</h2>
          <p className="text-xs text-gray-500">Powered by Ollama + Qdrant</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-400">Fontes:</span>
          <input
            type="range"
            min={1}
            max={20}
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            className="w-24 accent-blue-500 cursor-pointer"
          />
          <span className="text-xs font-mono text-blue-400 w-5 text-center">{topK}</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      <ChatInput onSend={handleSend} disabled={loading} />
    </div>
  )
}
