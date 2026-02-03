import { ChatContainer } from './components/ChatContainer'

/**
 * 앱 루트 컴포넌트
 * KB 스타일 RAG 챗봇
 */
function App() {
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

      {/* 채팅 영역 */}
      <main className="flex-1 overflow-hidden">
        <ChatContainer />
      </main>
    </div>
  )
}

export default App
