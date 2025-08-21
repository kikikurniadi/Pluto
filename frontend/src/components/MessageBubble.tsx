export default function MessageBubble({ message }: { message: { id: string; text: string; sender: 'user' | 'pluto' } }) {
  const isUser = message.sender === 'user'
  return (
    <div className={isUser ? 'flex justify-end' : 'flex justify-start'}>
      <div className={isUser ? 'bg-indigo-600 text-white px-3 py-2 rounded-md' : 'bg-slate-700 text-slate-100 px-3 py-2 rounded-md'}>
        {message.text}
      </div>
    </div>
  )
}
