import { useMemo } from 'react'
import { useChatStore } from '../store/chatStore'
import type { Message } from '../types/message'

/**
 * 메시지 관리 훅
 * 메시지 목록 조회 및 필터링
 * 
 * TODO: 추가 기능 구현 (Phase 5)
 */
export function useMessages() {
  const messages = useChatStore((state) => state.messages)
  const streamingContent = useChatStore((state) => state.streamingContent)
  const isLoading = useChatStore((state) => state.isLoading)

  // 사용자 메시지만 필터링
  const userMessages = useMemo(
    () => messages.filter((msg) => msg.role === 'user'),
    [messages]
  )

  // AI 메시지만 필터링
  const assistantMessages = useMemo(
    () => messages.filter((msg) => msg.role === 'assistant'),
    [messages]
  )

  // 마지막 메시지
  const lastMessage = useMemo(
    () => (messages.length > 0 ? messages[messages.length - 1] : null),
    [messages]
  )

  // 스트리밍 중인 메시지 (임시 메시지 객체)
  const streamingMessage: Message | null = useMemo(() => {
    if (streamingContent === null) return null
    return {
      id: 'streaming',
      sessionId: '',
      role: 'assistant',
      content: streamingContent,
      timestamp: new Date().toISOString(),
    }
  }, [streamingContent])

  // 표시할 전체 메시지 목록 (스트리밍 메시지 포함)
  const displayMessages = useMemo(() => {
    if (streamingMessage) {
      return [...messages, streamingMessage]
    }
    return messages
  }, [messages, streamingMessage])

  return {
    messages,
    displayMessages,
    userMessages,
    assistantMessages,
    lastMessage,
    streamingMessage,
    isLoading,
    messageCount: messages.length,
  }
}
