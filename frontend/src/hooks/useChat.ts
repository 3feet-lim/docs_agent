import { useCallback, useEffect } from 'react'
import {
  sendChatMessage,
  onChatResponseChunk,
  onChatResponseComplete,
  onChatError,
  offChatResponseChunk,
  offChatResponseComplete,
  offChatError,
} from '../api/socket'
import { useChatStore } from '../store/chatStore'
import type { Message } from '../types/message'

/**
 * 채팅 로직 훅
 * 메시지 전송 및 응답 처리
 * 
 * TODO: 실제 로직 완성 (Phase 5)
 */
export function useChat() {
  const {
    currentSessionId,
    messages,
    isLoading,
    streamingContent,
    error,
    setSessionId,
    addMessage,
    startStreaming,
    appendStreamingContent,
    completeStreaming,
    setError,
    startNewConversation,
  } = useChatStore()

  // 세션 초기화
  useEffect(() => {
    if (!currentSessionId) {
      startNewConversation()
    }
  }, [currentSessionId, startNewConversation])

  // 이벤트 리스너 등록
  useEffect(() => {
    // 스트리밍 청크 수신
    const handleChunk = (data: { content: string; isFinal: boolean }) => {
      appendStreamingContent(data.content)
    }

    // 응답 완료
    const handleComplete = (data: { messageId: string; sources: any[] }) => {
      completeStreaming(data.messageId, data.sources)
    }

    // 에러 처리
    const handleError = (error: { code: string; message: string }) => {
      setError({
        type: error.code as any,
        message: error.message,
        retryable: error.code === 'NETWORK_ERROR',
      })
    }

    onChatResponseChunk(handleChunk)
    onChatResponseComplete(handleComplete)
    onChatError(handleError)

    return () => {
      offChatResponseChunk(handleChunk)
      offChatResponseComplete(handleComplete)
      offChatError(handleError)
    }
  }, [appendStreamingContent, completeStreaming, setError])

  // 메시지 전송
  const sendMessage = useCallback(
    (content: string) => {
      if (!currentSessionId || !content.trim()) return

      // 사용자 메시지 추가
      const userMessage: Message = {
        id: `${Date.now()}-user`,
        sessionId: currentSessionId,
        role: 'user',
        content: content.trim(),
        timestamp: new Date().toISOString(),
      }
      addMessage(userMessage)

      // 스트리밍 시작
      startStreaming()

      // 서버로 전송
      sendChatMessage({
        sessionId: currentSessionId,
        message: content.trim(),
        timestamp: new Date().toISOString(),
      })
    },
    [currentSessionId, addMessage, startStreaming]
  )

  return {
    sessionId: currentSessionId,
    messages,
    isLoading,
    streamingContent,
    error,
    sendMessage,
    startNewConversation,
  }
}
