/**
 * 채팅 관련 타입 정의
 */

/**
 * 채팅 메시지 요청
 */
export interface ChatRequest {
  sessionId: string
  message: string
  timestamp: string
}

/**
 * 스트리밍 응답 청크
 */
export interface ChatResponseChunk {
  sessionId: string
  content: string
  isFinal: boolean
}

/**
 * 채팅 응답 완료
 */
export interface ChatResponseComplete {
  sessionId: string
  messageId: string
  sources: Array<{
    document: string
    page?: number
    similarity: number
  }>
}

/**
 * 채팅 에러
 */
export interface ChatError {
  sessionId: string
  code: string
  message: string
}
