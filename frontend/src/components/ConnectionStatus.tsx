import { Wifi, WifiOff } from 'lucide-react'
import { useUIStore } from '../store/uiStore'

/**
 * 연결 상태 표시 컴포넌트
 */
export function ConnectionStatus() {
  const { isConnected } = useUIStore()

  if (isConnected) return null

  return (
    <div className="bg-red-50 border-b border-red-200 px-4 py-2 flex items-center gap-2">
      <WifiOff size={16} className="text-red-500" />
      <span className="text-sm text-red-600">
        서버와 연결이 끊어졌습니다. 재연결 중...
      </span>
    </div>
  )
}
