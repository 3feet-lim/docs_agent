/**
 * HTTP 클라이언트
 * REST API 호출을 위한 유틸리티
 */

// 백엔드 URL (Vite proxy 사용)
const API_BASE = '/api'

/**
 * API 응답 타입
 */
interface ApiResponse<T> {
  data?: T
  error?: {
    code: string
    message: string
  }
}

/**
 * Health Check API
 */
export async function healthCheck(): Promise<ApiResponse<{ status: string; timestamp: string }>> {
  try {
    const response = await fetch(`${API_BASE}/health`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const data = await response.json()
    return { data }
  } catch (error) {
    return {
      error: {
        code: 'NETWORK_ERROR',
        message: error instanceof Error ? error.message : '알 수 없는 오류',
      },
    }
  }
}

/**
 * 세션 목록 조회 API
 */
export async function getSessions(): Promise<
  ApiResponse<{
    sessions: Array<{
      session_id: string
      message_count: number
      created_at: string
      updated_at: string
      first_message?: string
    }>
    count: number
  }>
> {
  try {
    const response = await fetch(`${API_BASE}/sessions`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const data = await response.json()
    return { data }
  } catch (error) {
    return {
      error: {
        code: 'NETWORK_ERROR',
        message: error instanceof Error ? error.message : '알 수 없는 오류',
      },
    }
  }
}

/**
 * 세션 히스토리 조회 API
 */
export async function getSessionHistory(sessionId: string): Promise<
  ApiResponse<{
    session_id: string
    messages: Array<{
      id: string
      session_id: string
      role: string
      content: string
      timestamp: string
      sources?: any[]
    }>
    count: number
  }>
> {
  try {
    const response = await fetch(`${API_BASE}/chat/${sessionId}/history`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const data = await response.json()
    return { data }
  } catch (error) {
    return {
      error: {
        code: 'NETWORK_ERROR',
        message: error instanceof Error ? error.message : '알 수 없는 오류',
      },
    }
  }
}

/**
 * 세션 삭제 API
 */
export async function deleteSession(sessionId: string): Promise<ApiResponse<{ message: string }>> {
  try {
    const response = await fetch(`${API_BASE}/chat/${sessionId}`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const data = await response.json()
    return { data }
  } catch (error) {
    return {
      error: {
        code: 'NETWORK_ERROR',
        message: error instanceof Error ? error.message : '알 수 없는 오류',
      },
    }
  }
}
