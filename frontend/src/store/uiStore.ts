import { create } from 'zustand'

interface UIState {
  isConnected: boolean
  isSidebarOpen: boolean

  // 액션
  setConnected: (isConnected: boolean) => void
  toggleSidebar: () => void
}

export const useUIStore = create<UIState>((set) => ({
  isConnected: true, // 초기값: 연결됨 (테스트용)
  isSidebarOpen: false,

  setConnected: (isConnected: boolean) => {
    set({ isConnected })
  },

  toggleSidebar: () => {
    set((state) => ({ isSidebarOpen: !state.isSidebarOpen }))
  },
}))
