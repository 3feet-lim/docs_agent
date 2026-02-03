import { Bot } from 'lucide-react'

/**
 * 타이핑 인디케이터 컴포넌트
 * AI가 응답을 생성 중일 때 표시
 */
export function TypingIndicator() {
  return (
    <div className="flex gap-3">
      {/* 아바타 */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center">
        <Bot className="w-5 h-5 text-white" />
      </div>

      {/* 타이핑 애니메이션 */}
      <div className="bg-gray-100 rounded-2xl rounded-bl-md px-4 py-3">
        <div className="flex gap-1">
          <div className="typing-dot" />
          <div className="typing-dot" />
          <div className="typing-dot" />
        </div>
      </div>
    </div>
  )
}
