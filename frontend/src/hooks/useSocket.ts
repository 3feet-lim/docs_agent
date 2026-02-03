import { useEffect, useCallback } from 'react'
import {
  initSocket,
  disconnectSocket,
  onConnect,
  onDisconnect,
  offConnect,
  offDisconnect,
} from '../api/socket'
import { useUIStore } from '../store/uiStore'

/**
 * Socket.IO 연결 관리 훅
 * 
 * TODO: 실제 연결 로직 완성 (Phase 5)
 */
export function useSocket() {
  const setConnectionStatus = useUIStore((state) => state.setConnectionStatus)

  // 연결 핸들러
  const handleConnect = useCallback(() => {
    console.log('Socket.IO 연결됨')
    setConnectionStatus('connected')
  }, [setConnectionStatus])

  // 연결 해제 핸들러
  const handleDisconnect = useCallback(
    (reason: string) => {
      console.log('Socket.IO 연결 해제:', reason)
      setConnectionStatus('disconnected')
    },
    [setConnectionStatus]
  )

  // 연결 초기화 및 정리
  useEffect(() => {
    setConnectionStatus('connecting')
    const socket = initSocket()

    onConnect(handleConnect)
    onDisconnect(handleDisconnect)

    // 이미 연결된 경우
    if (socket.connected) {
      setConnectionStatus('connected')
    }

    // 정리 함수
    return () => {
      offConnect(handleConnect)
      offDisconnect(handleDisconnect)
      disconnectSocket()
    }
  }, [handleConnect, handleDisconnect, setConnectionStatus])
}
