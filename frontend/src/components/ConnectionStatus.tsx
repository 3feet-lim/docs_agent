import { Wifi, WifiOff } from 'lucide-react'

/**
 * 연결 상태 컴포넌트
 * Socket.IO 연결 상태를 표시
 * 
 * TODO: 실제 연결 상태 연동 (Phase 5에서 구현)
 */
export function ConnectionStatus() {
  // 임시 연결 상태 (실제 구현 시 store에서 가져옴)
  const isConnected = true

  return (
    <div
      className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
        isConnected
          ? 'bg-green-100 text-green-700'
          : 'bg-red-100 text-red-700'
      }`}
    >
      {isConnected ? (
        <>
          <Wifi className="w-4 h-4" />
          <span>연결됨</span>
        </>
      ) : (
        <>
          <WifiOff className="w-4 h-4" />
          <span>연결 끊김</span>
        </>
      )}
    </div>
  )
}
