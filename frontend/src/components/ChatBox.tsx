import { useEffect, useRef } from 'react'
import { useChatStore } from '../store/useChatStore'
import MessageBubble from './MessageBubble'
import ChatInput from './ChatInput'

export default function ChatBox() {
  const messages = useChatStore((s) => s.messages)
  const containerRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    containerRef.current?.scrollTo({ top: containerRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages.length])

  return (
    <div className="bg-slate-800 rounded-lg p-4 shadow-md">
      <div ref={containerRef} className="space-y-3 h-96 overflow-y-auto mb-4">
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}
      </div>
      <ChatInput />
    </div>
  )
}
