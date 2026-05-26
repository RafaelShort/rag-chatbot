import { Message } from '../../types'
import { clsx } from 'clsx'

interface ChatMessageProps {
  message: Message
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'

  if (message.isLoading) {
    return (
      <div className="flex gap-3 items-start">
        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold shrink-0">AI</div>
        <div className="bg-gray-800 border border-gray-700 rounded-2xl rounded-tl-sm px-4 py-3">
          <div className="flex gap-1.5 items-center h-5">
            <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={clsx('flex gap-3 items-start', isUser && 'flex-row-reverse')}>
      <div className={clsx(
        'w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0',
        isUser ? 'bg-gray-700 text-gray-300' : 'bg-blue-600 text-white'
      )}>
        {isUser ? 'EU' : 'AI'}
      </div>

      <div className={clsx(
        'max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed',
        isUser
          ? 'bg-blue-600 text-white rounded-tr-sm'
          : 'bg-gray-800 border border-gray-700 text-gray-100 rounded-tl-sm'
      )}>
        <p className="whitespace-pre-wrap">{message.content}</p>

        {message.sources && message.sources.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-600">
            <p className="text-xs text-gray-400 mb-2 font-medium">
              {message.sources.length} fonte(s) encontrada(s)
            </p>
            <div className="flex flex-col gap-2">
              {message.sources.map((source, idx) => (
                <div key={idx} className="bg-gray-900/50 rounded-lg p-2 text-xs">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-blue-400 font-medium">Chunk #{source.chunk_index}</span>
                    <span className="text-gray-500">Score: {(source.score * 100).toFixed(0)}%</span>
                  </div>
                  <p className="text-gray-400 line-clamp-2">{source.content}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        <p className={clsx('text-xs mt-2', isUser ? 'text-blue-200' : 'text-gray-500')}>
          {message.timestamp.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>
    </div>
  )
}
