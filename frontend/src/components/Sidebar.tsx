import { useEffect } from 'react'
import { useChatStore } from '../store/chatStore'

/**
 * 사이드바 컴포넌트
 * 채팅 세션 목록 및 새 채팅 버튼
 */
export function Sidebar() {
  const {
    sessions,
    sessionId,
    isLoadingSessions,
    isSidebarOpen,
    loadSessions,
    loadSession,
    deleteSessionById,
    startNewChat,
    toggleSidebar,
  } = useChatStore()

  // 컴포넌트 마운트 시 세션 목록 로드
  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  // 날짜 포맷팅
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))

    if (days === 0) {
      return date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })
    } else if (days === 1) {
      return '어제'
    } else if (days < 7) {
      return `${days}일 전`
    } else {
      return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })
    }
  }

  // 세션 제목 생성 (첫 메시지 또는 기본값)
  const getSessionTitle = (session: typeof sessions[0]) => {
    if (session.firstMessage) {
      return session.firstMessage.length > 30
        ? session.firstMessage.slice(0, 30) + '...'
        : session.firstMessage
    }
    return `대화 ${session.messageCount}개`
  }

  if (!isSidebarOpen) {
    return (
      <button
        onClick={toggleSidebar}
        className="fixed left-0 top-1/2 -translate-y-1/2 bg-kb-yellow text-kb-black p-2 rounded-r-lg shadow-lg hover:bg-kb-yellow-dark transition-colors z-10"
        title="사이드바 열기"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>
    )
  }

  return (
    <aside className="w-72 bg-white border-r border-kb-gray-200 flex flex-col h-full">
      {/* 헤더 */}
      <div className="p-4 border-b border-kb-gray-200 flex items-center justify-between">
        <h2 className="font-semibold text-kb-black">대화 목록</h2>
        <button
          onClick={toggleSidebar}
          className="p-1 hover:bg-kb-gray-100 rounded transition-colors"
          title="사이드바 닫기"
        >
          <svg className="w-5 h-5 text-kb-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
      </div>

      {/* 새 채팅 버튼 */}
      <div className="p-3">
        <button
          onClick={startNewChat}
          className="w-full flex items-center gap-2 px-4 py-3 bg-kb-yellow text-kb-black rounded-lg hover:bg-kb-yellow-dark transition-colors font-medium"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          새 대화 시작
        </button>
      </div>

      {/* 세션 목록 */}
      <div className="flex-1 overflow-y-auto">
        {isLoadingSessions ? (
          <div className="p-4 text-center text-kb-gray-500">
            <div className="animate-spin w-6 h-6 border-2 border-kb-yellow border-t-transparent rounded-full mx-auto mb-2" />
            로딩 중...
          </div>
        ) : sessions.length === 0 ? (
          <div className="p-4 text-center text-kb-gray-500">
            <p>저장된 대화가 없습니다</p>
            <p className="text-sm mt-1">새 대화를 시작해보세요!</p>
          </div>
        ) : (
          <ul className="space-y-1 p-2">
            {sessions.map((session) => (
              <li key={session.sessionId}>
                <button
                  onClick={() => loadSession(session.sessionId)}
                  className={`w-full text-left p-3 rounded-lg transition-colors group ${
                    sessionId === session.sessionId
                      ? 'bg-kb-yellow-light border border-kb-yellow'
                      : 'hover:bg-kb-gray-100'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-kb-black truncate">
                        {getSessionTitle(session)}
                      </p>
                      <p className="text-xs text-kb-gray-500 mt-1">
                        {formatDate(session.updatedAt)} · {session.messageCount}개 메시지
                      </p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        if (confirm('이 대화를 삭제하시겠습니까?')) {
                          deleteSessionById(session.sessionId)
                        }
                      }}
                      className="p-1 opacity-0 group-hover:opacity-100 hover:bg-red-100 rounded transition-all"
                      title="삭제"
                    >
                      <svg className="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* 푸터 */}
      <div className="p-3 border-t border-kb-gray-200">
        <button
          onClick={loadSessions}
          className="w-full text-sm text-kb-gray-500 hover:text-kb-black transition-colors flex items-center justify-center gap-1"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          새로고침
        </button>
      </div>
    </aside>
  )
}
