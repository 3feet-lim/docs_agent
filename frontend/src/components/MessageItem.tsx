import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import type { Message } from '../types/message'

interface MessageItemProps {
  message: Message
}

/**
 * 개별 메시지 컴포넌트
 * 사용자/AI 메시지를 구분하여 표시
 */
export function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-3 message-enter ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* 아바타 */}
      <div className="flex-shrink-0">
        {isUser ? (
          <div className="w-10 h-10 rounded-full bg-kb-yellow flex items-center justify-center">
            <span className="text-white font-semibold text-sm">나</span>
          </div>
        ) : (
          <img 
            src="/kb-character-bibi.png" 
            alt="비비" 
            className="w-10 h-10 object-contain"
          />
        )}
      </div>

      {/* 메시지 내용 */}
      <div className={`flex flex-col max-w-[70%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`px-4 py-3 rounded-2xl ${
            isUser
              ? 'bg-kb-yellow text-kb-black rounded-tr-sm'
              : 'bg-white border border-kb-gray-200 text-kb-gray-800 rounded-tl-sm shadow-sm'
          }`}
        >
          <p className="whitespace-pre-wrap text-sm leading-relaxed">
            {message.content}
          </p>
        </div>

        {/* 타임스탬프 */}
        <span className="text-xs text-kb-gray-400 mt-1 px-1">
          {format(new Date(message.timestamp), 'a h:mm', { locale: ko })}
        </span>

        {/* 출처 정보 (AI 메시지만) */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-2 px-1">
            <p className="text-xs text-kb-gray-500 mb-1">📄 참고 문서:</p>
            <div className="flex flex-wrap gap-1">
              {message.sources.map((source, idx) => (
                <span 
                  key={idx}
                  className="text-xs bg-kb-yellow-light text-kb-gray-700 px-2 py-0.5 rounded"
                >
                  {source.document}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
