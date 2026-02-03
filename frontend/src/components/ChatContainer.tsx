import { MessageList } from './MessageList'
import { MessageInput } from './MessageInput'
import { ConnectionStatus } from './ConnectionStatus'

/**
 * 채팅 컨테이너 컴포넌트
 * 채팅 UI의 메인 레이아웃을 담당
 */
export function ChatContainer() {
  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto bg-white shadow-lg">
      {/* 헤더 */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-white">
        <h1 className="text-xl font-semibold text-gray-800">RAG 챗봇</h1>
        <ConnectionStatus />
      </header>

      {/* 메시지 목록 */}
      <main className="flex-1 overflow-y-auto">
        <MessageList />
      </main>

      {/* 입력창 */}
      <footer className="border-t border-gray-200 bg-white">
        <MessageInput />
      </footer>
    </div>
  )
}
