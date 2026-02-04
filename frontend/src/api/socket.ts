import { io, Socket } from 'socket.io-client'
import type { SendMessageRequest } from '../types/chat'
import type { MessageChunk, MessageComplete } from '../types/message'

/**
 * Socket.IO 클라이언트 설정
 * 
 * TODO: 실제 연결 로직 구현 (Phase 5)
 */

// 백엔드 URL (환경변수 또는 기본값 - 빈 문자열이면 같은 호스트 사용)
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || ''

// Socket.IO 클라이언트 인스턴스
let socket: Socket | null = null

/**
 * Socket.IO 연결 초기화
 */
export function initSocket(): Socket {
  if (socket) {
    return socket
  }

  // BACKEND_URL이 비어있으면 현재 호스트 사용 (Vite proxy 활용)
  const socketUrl = BACKEND_URL || window.location.origin

  socket = io(socketUrl, {
    transports: ['websocket', 'polling'],
    autoConnect: true,
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    path: '/socket.io',
  })

  return socket
}

/**
 * Socket.IO 연결 해제
 */
export function disconnectSocket(): void {
  if (socket) {
    socket.disconnect()
    socket = null
  }
}

/**
 * Socket.IO 인스턴스 가져오기
 */
export function getSocket(): Socket | null {
  return socket
}

/**
 * 채팅 메시지 전송
 */
export function sendChatMessage(request: SendMessageRequest): void {
  if (socket && socket.connected) {
    socket.emit('chat_message', request)
  } else {
    console.error('Socket이 연결되지 않았습니다.')
  }
}

/**
 * 이벤트 리스너 등록 헬퍼 함수들
 */
export function onConnect(callback: () => void): void {
  socket?.on('connect', callback)
}

export function onDisconnect(callback: (reason: string) => void): void {
  socket?.on('disconnect', callback)
}

export function onChatResponseChunk(callback: (data: MessageChunk) => void): void {
  socket?.on('chat_response_chunk', callback)
}

export function onChatResponseComplete(callback: (data: MessageComplete) => void): void {
  socket?.on('chat_response_complete', callback)
}

export function onChatError(callback: (error: { code: string; message: string }) => void): void {
  socket?.on('chat_error', callback)
}

/**
 * 이벤트 리스너 제거 헬퍼 함수들
 */
export function offConnect(callback?: () => void): void {
  socket?.off('connect', callback)
}

export function offDisconnect(callback?: (reason: string) => void): void {
  socket?.off('disconnect', callback)
}

export function offChatResponseChunk(callback?: (data: MessageChunk) => void): void {
  socket?.off('chat_response_chunk', callback)
}

export function offChatResponseComplete(callback?: (data: MessageComplete) => void): void {
  socket?.off('chat_response_complete', callback)
}

export function offChatError(callback?: (error: { code: string; message: string }) => void): void {
  socket?.off('chat_error', callback)
}
