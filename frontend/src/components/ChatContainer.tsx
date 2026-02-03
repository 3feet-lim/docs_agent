import { useRef, useEffect } from 'react'
import { MessageList } from './MessageList'
import { MessageInput } from './MessageInput'
import { ConnectionStatus } from './ConnectionStatus'
import { useChatStore } from '../store/chatStore'

/**
 * 채팅 컨테이너 컴포넌트
 * 메시지 목록과 입력창을 포함
 */
export function ChatContainer() {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { messages } = useChatStore()

  // 새 메시지 시 스크롤 하단 이동
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="h-full flex flex-col max-w-4xl mx-auto w-full">
      {/* 연결 상태 */}
      <ConnectionStatus />

      {/* 메시지 목록 */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        {messages.length === 0 ? (
          <WelcomeMessage />
        ) : (
          <MessageList />
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 입력창 */}
      <div className="border-t border-kb-gray-200 bg-white p-4">
        <MessageInput />
      </div>
    </div>
  )
}

/**
 * 환영 메시지 컴포넌트
 */
function WelcomeMessage() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center py-12">
      <img 
        src="/kb-character-bibi.png" 
        alt="비비" 
        className="w-24 h-24 object-contain mb-4"
      />
      <h2 className="text-xl font-semibold text-kb-black mb-2">
        안녕하세요! KB AI 문서 도우미입니다
      </h2>
      <p className="text-kb-gray-500 max-w-md">
        사내 문서에 대해 궁금한 점을 물어보세요.
        관련 문서를 찾아 정확한 답변을 드릴게요.
      </p>
    </div>
  )
}
