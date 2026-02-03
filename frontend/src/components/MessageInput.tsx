import { useState, KeyboardEvent } from 'react'
import { Send } from 'lucide-react'
import { useChatStore } from '../store/chatStore'

/**
 * 메시지 입력 컴포넌트
 */
export function MessageInput() {
  const [input, setInput] = useState('')
  const { sendMessage, isTyping } = useChatStore()

  const handleSubmit = () => {
    const trimmed = input.trim()
    if (!trimmed || isTyping) return

    sendMessage(trimmed)
    setInput('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="flex items-end gap-3">
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="메시지를 입력하세요..."
        rows={1}
        className="flex-1 resize-none rounded-xl border border-kb-gray-300 px-4 py-3 text-sm
                   focus:outline-none focus:ring-2 focus:ring-kb-yellow focus:border-transparent
                   placeholder:text-kb-gray-400"
        style={{ maxHeight: '120px' }}
      />
      <button
        onClick={handleSubmit}
        disabled={!input.trim() || isTyping}
        className="flex-shrink-0 w-11 h-11 rounded-xl bg-kb-yellow text-white
                   flex items-center justify-center
                   hover:bg-kb-yellow-dark transition-colors
                   disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Send size={20} />
      </button>
    </div>
  )
}
