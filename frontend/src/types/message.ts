/**
 * 메시지 출처 정보 타입
 */
export interface Source {
  /** 문서 파일명 */
  document: string
  /** 페이지 번호 (선택) */
  page?: number
  /** 청크 ID */
  chunkId: string
  /** 유사도 점수 */
  similarity: number
  /** 청크 내용 */
  content: string
}

/**
 * 메시지 역할 타입
 */
export type MessageRole = 'user' | 'assistant'

/**
 * 메시지 타입
 */
export interface Message {
  /** 메시지 고유 ID */
  id: string
  /** 세션 ID */
  sessionId: string
  /** 메시지 역할 (사용자/AI) */
  role: MessageRole
  /** 메시지 내용 */
  content: string
  /** 타임스탬프 (ISO 8601 형식) */
  timestamp: string
  /** 출처 정보 (AI 응답에만 포함) */
  sources?: Source[]
}

/**
 * 스트리밍 메시지 청크 타입
 */
export interface MessageChunk {
  /** 세션 ID */
  sessionId: string
  /** 청크 내용 */
  content: string
  /** 최종 청크 여부 */
  isFinal: boolean
}

/**
 * 메시지 완료 응답 타입
 */
export interface MessageComplete {
  /** 세션 ID */
  sessionId: string
  /** 메시지 ID */
  messageId: string
  /** 출처 정보 */
  sources: Source[]
}
