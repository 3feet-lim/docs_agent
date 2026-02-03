import { ChatContainer } from './components/ChatContainer'

/**
 * 앱 루트 컴포넌트
 * RAG 챗봇 시스템의 메인 진입점
 */
function App() {
  return (
    <div className="min-h-screen bg-gray-100">
      <ChatContainer />
    </div>
  )
}

export default App
