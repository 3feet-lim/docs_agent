import { useEffect } from 'react'
import { ChatContainer } from './components/ChatContainer'
import { Sidebar } from './components/Sidebar'
import { useSocket } from './hooks/useSocket'
import { useChatStore } from './store/chatStore'
import {
  onChatResponseChunk,
  onChatResponseComplete,
  onChatError,
  offChatResponseChunk,
  offChatResponseComplete,
  offChatError,
} from './api/socket'

/**
 * 앱 루트 컴포넌트
 * KB 스타일 RAG 챗봇
 */
function App() {
  // Socket.IO 연결 관리
  useSocket()
  
  const { appendToStreaming, completeStreaming, setTyping, isSidebarOpen } = useChatStore()

  // Socket.IO 이벤트 리스너 등록
  useEffect(() => {
    const handleChunk = (data: { content: string; is_final: boolean }) => {
      appendToStreaming(data.content)
    }

    const handleComplete = (data: { message_id: string; sources: any[] }) => {
      const sources = data.sources?.map(s => ({
        document: s.document,
        sourceUri: s.source_uri,
        score: s.score,
        content: '',
        chunkId: '',
        similarity: s.score,
      })) || []
      completeStreaming(data.message_id, sources)
    }

    const handleError = (error: { code: string; message: string }) => {
      console.error('채팅 오류:', error)
      setTyping(false)
    }

    onChatResponseChunk(handleChunk)
    onChatResponseComplete(handleComplete)
    onChatError(handleError)

    return () => {
      offChatResponseChunk(handleChunk)
      offChatResponseComplete(handleComplete)
      offChatError(handleError)
    }
  }, [appendToStreaming, completeStreaming, setTyping])

  return (
    <div className="min-h-screen bg-kb-gray-50 flex flex-col">
      {/* 헤더 */}
      <header className="bg-white border-b border-kb-gray-200 px-4 py-3 flex items-center gap-3 shadow-sm">
        <img 
          src="/kb-logo.png" 
          alt="KB국민은행" 
          className="h-8 object-contain"
        />
        <div className="h-6 w-px bg-kb-gray-200" />
        <h1 className="text-lg font-semibold text-kb-black">
          AI 문서 도우미
        </h1>
      </header>

      {/* 메인 영역 (사이드바 + 채팅) */}
      <main className="flex-1 flex overflow-hidden">
        {/* 사이드바 */}
        <Sidebar />
        
        {/* 채팅 영역 */}
        <div className={`flex-1 overflow-hidden transition-all ${isSidebarOpen ? '' : 'ml-0'}`}>
          <ChatContainer />
        </div>
      </main>
    </div>
  )
}

export default App
