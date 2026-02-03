import { create } from 'zustand'
import type { Message, Source } from '../types/message'
import type { ChatError } from '../types/chat'

/**
 * 채팅 스토어 상태 인터페이스
 */
interface ChatState {
  /** 현재 세션 ID */
  currentSessionId: string | null
  /** 메시지 목록 */
  messages: Message[]
  /** 로딩 상태 (AI 응답 대기 중) */
  isLoading: boolean
  /** 스트리밍 중인 메시지 내용 */
  streamingContent: string | null
  /** 에러 정보 */
  error: ChatError | null
}

/**
 * 채팅 스토어 액션 인터페이스
 */
interface ChatActions {
  /** 세션 ID 설정 */
  setSessionId: (sessionId: string) => void
  /** 메시지 추가 */
  addMessage: (message: Message) => void
  /** 스트리밍 시작 */
  startStreaming: () => void
  /** 스트리밍 내용 추가 */
  appendStreamingContent: (content: string) => void
  /** 스트리밍 완료 */
  completeStreaming: (messageId: string, sources?: Source[]) => void
  /** 로딩 상태 설정 */
  setLoading: (isLoading: boolean) => void
  /** 에러 설정 */
  setError: (error: ChatError | null) => void
  /** 대화 초기화 */
  clearMessages: () => void
  /** 새 대화 시작 */
  startNewConversation: () => void
}

/**
 * 고유 ID 생성 함수
 */
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
}

/**
 * 채팅 상태 관리 스토어 (Zustand)
 * 
 * TODO: 실제 Socket.IO 연동 시 액션 구현 완료 (Phase 5)
 */
export const useChatStore = create<ChatState & ChatActions>((set, get) => ({
  // 초기 상태
  currentSessionId: null,
  messages: [],
  isLoading: false,
  streamingContent: null,
  error: null,

  // 액션
  setSessionId: (sessionId) => set({ currentSessionId: sessionId }),

  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),

  startStreaming: () =>
    set({
      isLoading: true,
      streamingContent: '',
    }),

  appendStreamingContent: (content) =>
    set((state) => ({
      streamingContent: (state.streamingContent || '') + content,
    })),

  completeStreaming: (messageId, sources) => {
    const { streamingContent, currentSessionId } = get()
    if (streamingContent !== null && currentSessionId) {
      const message: Message = {
        id: messageId,
        sessionId: currentSessionId,
        role: 'assistant',
        content: streamingContent,
        timestamp: new Date().toISOString(),
        sources,
      }
      set((state) => ({
        messages: [...state.messages, message],
        streamingContent: null,
        isLoading: false,
      }))
    }
  },

  setLoading: (isLoading) => set({ isLoading }),

  setError: (error) => set({ error }),

  clearMessages: () => set({ messages: [] }),

  startNewConversation: () =>
    set({
      currentSessionId: generateId(),
      messages: [],
      streamingContent: null,
      error: null,
    }),
}))
