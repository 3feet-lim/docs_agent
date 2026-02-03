/**
 * 타이핑 인디케이터 컴포넌트
 * AI가 응답을 생성 중일 때 표시
 */
export function TypingIndicator() {
  return (
    <div className="flex gap-3 message-enter">
      {/* 아바타 */}
      <img 
        src="/kb-character-bibi.png" 
        alt="비비" 
        className="w-10 h-10 object-contain flex-shrink-0"
      />

      {/* 타이핑 애니메이션 */}
      <div className="bg-white border border-kb-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
        <div className="flex gap-1">
          <span className="typing-dot w-2 h-2 bg-kb-gray-400 rounded-full" />
          <span className="typing-dot w-2 h-2 bg-kb-gray-400 rounded-full" />
          <span className="typing-dot w-2 h-2 bg-kb-gray-400 rounded-full" />
        </div>
      </div>
    </div>
  )
}
