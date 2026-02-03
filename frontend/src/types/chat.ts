import type { Message } from './message'

/**
 * 연결 상태 타입
 */
export type ConnectionStatus = 'connected' | 'disconnected' | 'connecting' | 'error'

/**
 * 채팅 세션 타입
 */
export interface ChatSession {
  /** 세션 ID */
  id: string
  /** 세션 생성 시간 */
  createdAt: string
  /** 마지막 활동 시간 */
  lastActivityAt: string
  /** 메시지 목록 */
  messages: Message[]
}

/**
 * 채팅 에러 타입
 */
export type ChatErrorType =
  | 'NETWORK_ERROR'
  | 'BEDROCK_ERROR'
  | 'VALIDATION_ERROR'
  | 'UNKNOWN_ERROR'

/**
 * 채팅 에러 인터페이스
 */
export interface ChatError {
  /** 에러 타입 */
  type: ChatErrorType
  /** 에러 메시지 */
  message: string
  /** 재시도 가능 여부 */
  retryable: boolean
}

/**
 * 채팅 메시지 전송 요청 타입
 */
export interface SendMessageRequest {
  /** 세션 ID */
  sessionId: string
  /** 메시지 내용 */
  message: string
  /** 타임스탬프 */
  timestamp: string
}

/**
 * 채팅 상태 타입
 */
export interface ChatState {
  /** 현재 세션 ID */
  currentSessionId: string | null
  /** 메시지 목록 */
  messages: Message[]
  /** 로딩 상태 */
  isLoading: boolean
  /** 스트리밍 중인 메시지 */
  streamingMessage: string | null
  /** 에러 정보 */
  error: ChatError | null
}
