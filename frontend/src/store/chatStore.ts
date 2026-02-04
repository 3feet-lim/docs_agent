import { create } from 'zustand'
import { sendChatMessage } from '../api/socket'
import type { Message, Source } from '../types/message'

interface ChatState {
  messages: Message[]
  isTyping: boolean
  sessionId: string
  streamingMessageId: string | null
  streamingContent: string

  // 액션
  sendMessage: (content: string) => void
  addMessage: (message: Message) => void
  appendToStreaming: (content: string) => void
  completeStreaming: (messageId: string, sources?: Source[]) => void
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
  streamingMessageId: null,
  streamingContent: '',

  sendMessage: (content: string) => {
    const state = get()
    
    // 사용자 메시지 추가
    const userMessage: Message = {
      id: generateMessageId(),
      sessionId: state.sessionId,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }

    // AI 응답 플레이스홀더 추가
    const aiMessageId = generateMessageId()
    const aiMessage: Message = {
      id: aiMessageId,
      sessionId: state.sessionId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
    }

    set({
      messages: [...state.messages, userMessage, aiMessage],
      isTyping: true,
      streamingMessageId: aiMessageId,
      streamingContent: '',
    })

    // Socket.IO로 메시지 전송
    sendChatMessage({
      sessionId: state.sessionId,
      message: content,
      timestamp: new Date().toISOString(),
    })
  },

  addMessage: (message: Message) => {
    set((state) => ({
      messages: [...state.messages, message],
    }))
  },

  appendToStreaming: (content: string) => {
    set((state) => {
      const newContent = state.streamingContent + content
      
      // 마지막 메시지 업데이트
      const messages = [...state.messages]
      if (messages.length > 0 && state.streamingMessageId) {
        const lastIndex = messages.findIndex(m => m.id === state.streamingMessageId)
        if (lastIndex !== -1) {
          messages[lastIndex] = {
            ...messages[lastIndex],
            content: newContent,
          }
        }
      }
      
      return { 
        messages,
        streamingContent: newContent 
      }
    })
  },

  completeStreaming: (messageId: string, sources?: Source[]) => {
    set((state) => {
      const messages = [...state.messages]
      const msgIndex = messages.findIndex(m => m.id === state.streamingMessageId)
      
      if (msgIndex !== -1 && sources) {
        messages[msgIndex] = {
          ...messages[msgIndex],
          sources,
        }
      }
      
      return {
        messages,
        isTyping: false,
        streamingMessageId: null,
        streamingContent: '',
      }
    })
  },

  setTyping: (isTyping: boolean) => {
    set({ isTyping })
  },

  clearMessages: () => {
    set({
      messages: [],
      sessionId: generateSessionId(),
      streamingMessageId: null,
      streamingContent: '',
    })
  },
}))
