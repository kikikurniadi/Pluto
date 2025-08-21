import { useState } from 'react'
import { useChatStore } from '../store/useChatStore'
import { sendQuery } from '../apiService'

export default function ChatInput() {
  const [value, setValue] = useState('')
  const [loading, setLoading] = useState(false)
  const addMessage = useChatStore((s) => s.addMessage)

  async function handleSend() {
    if (!value.trim()) return
    const userText = value.trim()
    addMessage({ id: String(Date.now()), text: userText, sender: 'user' })
    setValue('')
    setLoading(true)

    const res = await sendQuery(userText)
    setLoading(false)
    if (res.success) {
      addMessage({ id: String(Date.now() + 1), text: res.reply ?? 'No reply', sender: 'pluto' })
    } else {
      addMessage({ id: String(Date.now() + 1), text: `Error: ${res.error}`, sender: 'pluto' })
    }
  }

  return (
    <div className="flex gap-2">
      <input
        value={value}
        onChange={(e) => setValue((e.target as HTMLInputElement).value)}
        className="flex-1 px-3 py-2 rounded-md bg-slate-700"
        placeholder="Ask Pluto about crypto..."
      />
      <button onClick={handleSend} className="btn" disabled={loading}>{loading ? '...' : 'Send'}</button>
    </div>
  )
}
