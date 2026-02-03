import { MessageItem } from './MessageItem'
import { TypingIndicator } from './TypingIndicator'
import { useChatStore } from '../store/chatStore'

/**
 * 메시지 목록 컴포넌트
 */
export function MessageList() {
  const { messages, isTyping } = useChatStore()

  return (
    <div className="space-y-4">
      {messages.map((message) => (
        <MessageItem key={message.id} message={message} />
      ))}
      {isTyping && <TypingIndicator />}
    </div>
  )
}
