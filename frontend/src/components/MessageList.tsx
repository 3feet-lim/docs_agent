import { MessageItem } from './MessageItem'
import { TypingIndicator } from './TypingIndicator'
import type { Message } from '../types/message'

/**
 * 메시지 목록 컴포넌트
 * 채팅 메시지들을 렌더링
 * 
 * TODO: 실제 메시지 데이터 연동 (Phase 5에서 구현)
 */
export function MessageList() {
  // 임시 데모 메시지 (실제 구현 시 store에서 가져옴)
  const messages: Message[] = [
    {
      id: '1',
      sessionId: 'demo',
      role: 'assistant',
      content: '안녕하세요! RAG 챗봇입니다. 사내 문서에 대해 질문해 주세요.',
      timestamp: new Date().toISOString(),
    },
  ]

  // 타이핑 상태 (실제 구현 시 store에서 가져옴)
  const isTyping = false

  return (
    <div className="p-4 space-y-4">
      {messages.map((message) => (
        <MessageItem key={message.id} message={message} />
      ))}
      {isTyping && <TypingIndicator />}
    </div>
  )
}
