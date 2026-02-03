/**
 * 메시지 타입 정의
 */
export interface Message {
  id: string
  sessionId: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  sources?: Source[]
}

/**
 * 출처 정보 타입
 */
export interface Source {
  document: string
  page?: number
  chunkId: string
  similarity: number
  content: string
}
