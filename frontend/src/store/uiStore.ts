import { create } from 'zustand'
import type { ConnectionStatus } from '../types/chat'

/**
 * UI 스토어 상태 인터페이스
 */
interface UIState {
  /** Socket.IO 연결 상태 */
  connectionStatus: ConnectionStatus
  /** 사이드바 열림 상태 */
  isSidebarOpen: boolean
  /** 다크 모드 */
  isDarkMode: boolean
}

/**
 * UI 스토어 액션 인터페이스
 */
interface UIActions {
  /** 연결 상태 설정 */
  setConnectionStatus: (status: ConnectionStatus) => void
  /** 사이드바 토글 */
  toggleSidebar: () => void
  /** 사이드바 열기/닫기 */
  setSidebarOpen: (isOpen: boolean) => void
  /** 다크 모드 토글 */
  toggleDarkMode: () => void
}

/**
 * UI 상태 관리 스토어 (Zustand)
 * 
 * TODO: 실제 연결 상태 연동 (Phase 5)
 */
export const useUIStore = create<UIState & UIActions>((set) => ({
  // 초기 상태
  connectionStatus: 'disconnected',
  isSidebarOpen: false,
  isDarkMode: false,

  // 액션
  setConnectionStatus: (status) => set({ connectionStatus: status }),

  toggleSidebar: () =>
    set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),

  setSidebarOpen: (isOpen) => set({ isSidebarOpen: isOpen }),

  toggleDarkMode: () =>
    set((state) => ({ isDarkMode: !state.isDarkMode })),
}))
