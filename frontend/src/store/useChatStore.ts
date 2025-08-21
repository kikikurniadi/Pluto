import create from 'zustand'

type Message = { id: string; text: string; sender: 'user' | 'pluto' }

type ChatState = {
  messages: Message[]
  addMessage: (m: Message) => void
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  addMessage: (m) => set((s) => ({ messages: [...s.messages, m] })),
}))

export default useChatStore
