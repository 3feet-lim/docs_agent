import { create } from 'zustand'
import { sendChatMessage } from '../api/socket'
import { getSessions, getSessionHistory, deleteSession } from '../api/http'
import type { Message, Source } from '../types/message'

interface Session {
  sessionId: string
  messageCount: number
  createdAt: string
  updatedAt: string
  firstMessage?: string
}

interface ChatState {
  messages: Message[]
  isTyping: boolean
  sessionId: string
  streamingMessageId: string | null
  streamingContent: string
  sessions: Session[]
  isLoadingSessions: boolean
  isSidebarOpen: boolean

  // 액션
  sendMessage: (content: string) => void
  addMessage: (message: Message) => void
  appendToStreaming: (content: string) => void
  completeStreaming: (messageId: string, sources?: Source[]) => void
  setTyping: (isTyping: boolean) => void
  clearMessages: () => void
  loadSessions: () => Promise<void>
  loadSession: (sessionId: string) => Promise<void>
  deleteSessionById: (sessionId: string) => Promise<void>
  startNewChat: () => void
  toggleSidebar: () => void
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
  sessions: [],
  isLoadingSessions: false,
  isSidebarOpen: true,

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
    
    // 응답 완료 후 세션 목록 새로고침
    get().loadSessions()
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

  loadSessions: async () => {
    set({ isLoadingSessions: true })
    try {
      const response = await getSessions()
      if (response.data) {
        const sessions: Session[] = response.data.sessions.map(s => ({
          sessionId: s.session_id,
          messageCount: s.message_count,
          createdAt: s.created_at,
          updatedAt: s.updated_at,
          firstMessage: s.first_message,
        }))
        set({ sessions })
      }
    } catch (error) {
      console.error('세션 목록 로드 실패:', error)
    } finally {
      set({ isLoadingSessions: false })
    }
  },

  loadSession: async (sessionId: string) => {
    try {
      const response = await getSessionHistory(sessionId)
      if (response.data) {
        const messages: Message[] = response.data.messages.map(m => ({
          id: m.id,
          sessionId: m.session_id,
          role: m.role as 'user' | 'assistant',
          content: m.content,
          timestamp: m.timestamp,
          sources: m.sources?.map(s => ({
            document: s.document,
            sourceUri: s.source_uri,
            score: s.score,
            content: '',
            chunkId: '',
            similarity: s.score,
          })),
        }))
        set({ 
          messages, 
          sessionId,
          streamingMessageId: null,
          streamingContent: '',
        })
      }
    } catch (error) {
      console.error('세션 로드 실패:', error)
    }
  },

  deleteSessionById: async (sessionId: string) => {
    try {
      await deleteSession(sessionId)
      // 현재 세션이 삭제된 경우 새 채팅 시작
      if (get().sessionId === sessionId) {
        get().startNewChat()
      }
      // 세션 목록 새로고침
      get().loadSessions()
    } catch (error) {
      console.error('세션 삭제 실패:', error)
    }
  },

  startNewChat: () => {
    set({
      messages: [],
      sessionId: generateSessionId(),
      streamingMessageId: null,
      streamingContent: '',
      isTyping: false,
    })
  },

  toggleSidebar: () => {
    set((state) => ({ isSidebarOpen: !state.isSidebarOpen }))
  },
}))
