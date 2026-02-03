import { useState, useCallback, KeyboardEvent } from 'react'
import { Send } from 'lucide-react'

/**
 * 메시지 입력 컴포넌트
 * 사용자 메시지 입력 및 전송 처리
 * 
 * TODO: 실제 메시지 전송 로직 연동 (Phase 5에서 구현)
 */
export function MessageInput() {
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  // 메시지 전송 핸들러
  const handleSend = useCallback(() => {
    if (!message.trim() || isLoading) return

    // TODO: 실제 전송 로직 구현
    console.log('메시지 전송:', message)
    setMessage('')
  }, [message, isLoading])

  // Enter 키 전송 핸들러
  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSend()
      }
    },
    [handleSend]
  )

  return (
    <div className="p-4">
      <div className="flex items-end gap-2">
        {/* 입력창 */}
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="메시지를 입력하세요..."
          className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent min-h-[48px] max-h-[200px]"
          rows={1}
          disabled={isLoading}
        />

        {/* 전송 버튼 */}
        <button
          onClick={handleSend}
          disabled={!message.trim() || isLoading}
          className="flex-shrink-0 w-12 h-12 rounded-xl bg-blue-500 text-white flex items-center justify-center hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          <Send className="w-5 h-5" />
        </button>
      </div>

      {/* 안내 문구 */}
      <p className="text-xs text-gray-400 mt-2 text-center">
        Enter로 전송, Shift+Enter로 줄바꿈
      </p>
    </div>
  )
}
