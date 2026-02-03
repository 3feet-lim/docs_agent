import { create } from 'zustand'
import type { Message, Source } from '../types/message'

interface ChatState {
  messages: Message[]
  isTyping: boolean
  sessionId: string

  // 액션
  sendMessage: (content: string) => void
  addMessage: (message: Message) => void
  updateLastMessage: (content: string) => void
  setTyping: (isTyping: boolean) => void
  clearMessages: () => void
}

// 세션 ID 생성
const generateSessionId = () => `session_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`

// 메시지 ID 생성
const generateMessageId = () => `msg_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isTyping: false,
  sessionId: generateSessionId(),

  sendMessage: (content: string) => {
    const userMessage: Message = {
      id: generateMessageId(),
      sessionId: get().sessionId,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }

    set((state) => ({
      messages: [...state.messages, userMessage],
      isTyping: true,
    }))

    // TODO: Socket.IO로 메시지 전송
    // 임시로 더미 응답 추가 (테스트용)
    setTimeout(() => {
      const aiMessage: Message = {
        id: generateMessageId(),
        sessionId: get().sessionId,
        role: 'assistant',
        content: '안녕하세요! KB AI 문서 도우미입니다. 현재 백엔드 서버가 연결되지 않아 테스트 응답을 보여드리고 있습니다. 실제 서비스에서는 사내 문서를 기반으로 정확한 답변을 드릴 예정입니다.',
        timestamp: new Date().toISOString(),
        sources: [
          { document: 'user_manual.pdf', chunkId: 'chunk_001', similarity: 0.92, content: '' }
        ]
      }

      set((state) => ({
        messages: [...state.messages, aiMessage],
        isTyping: false,
      }))
    }, 1500)
  },

  addMessage: (message: Message) => {
    set((state) => ({
      messages: [...state.messages, message],
    }))
  },

  updateLastMessage: (content: string) => {
    set((state) => {
      const messages = [...state.messages]
      if (messages.length > 0) {
        messages[messages.length - 1] = {
          ...messages[messages.length - 1],
          content,
        }
      }
      return { messages }
    })
  },

  setTyping: (isTyping: boolean) => {
    set({ isTyping })
  },

  clearMessages: () => {
    set({
      messages: [],
      sessionId: generateSessionId(),
    })
  },
}))
