import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import { User, Bot } from 'lucide-react'
import type { Message } from '../types/message'

interface MessageItemProps {
  message: Message
}

/**
 * 개별 메시지 컴포넌트
 * 사용자/AI 메시지를 구분하여 렌더링
 */
export function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* 아바타 */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? 'bg-blue-500' : 'bg-gray-600'
        }`}
      >
        {isUser ? (
          <User className="w-5 h-5 text-white" />
        ) : (
          <Bot className="w-5 h-5 text-white" />
        )}
      </div>

      {/* 메시지 내용 */}
      <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-[70%]`}>
        <div
          className={`px-4 py-2 rounded-2xl ${
            isUser
              ? 'bg-blue-500 text-white rounded-br-md'
              : 'bg-gray-100 text-gray-800 rounded-bl-md'
          }`}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>

        {/* 타임스탬프 */}
        <span className="text-xs text-gray-400 mt-1">
          {format(new Date(message.timestamp), 'a h:mm', { locale: ko })}
        </span>

        {/* 출처 정보 (있는 경우) */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-2 text-xs text-gray-500">
            <span className="font-medium">출처: </span>
            {message.sources.map((source, index) => (
              <span key={source.chunkId}>
                {source.document}
                {source.page && ` (p.${source.page})`}
                {index < message.sources!.length - 1 && ', '}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
