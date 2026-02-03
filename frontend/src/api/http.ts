/**
 * HTTP 클라이언트
 * REST API 호출을 위한 유틸리티
 * 
 * TODO: 실제 API 연동 (Phase 5)
 */

// 백엔드 URL (환경변수 또는 기본값)
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

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
    const response = await fetch(`${BACKEND_URL}/api/health`)
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
 * 문서 목록 조회 API (선택)
 */
export async function getDocuments(): Promise<
  ApiResponse<{
    documents: Array<{
      id: string
      filename: string
      uploadedAt: string
      chunks: number
    }>
  }>
> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/documents`)
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
 * 문서 업로드 API (선택)
 */
export async function uploadDocument(
  file: File
): Promise<ApiResponse<{ id: string; filename: string; status: string }>> {
  try {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${BACKEND_URL}/api/documents/upload`, {
      method: 'POST',
      body: formData,
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
