import { create } from 'zustand'

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected'

interface UIState {
  isConnected: boolean
  connectionStatus: ConnectionStatus
  isSidebarOpen: boolean

  // 액션
  setConnected: (isConnected: boolean) => void
  setConnectionStatus: (status: ConnectionStatus) => void
  toggleSidebar: () => void
}

export const useUIStore = create<UIState>((set) => ({
  isConnected: false,
  connectionStatus: 'connecting',
  isSidebarOpen: false,

  setConnected: (isConnected: boolean) => {
    set({ isConnected })
  },

  setConnectionStatus: (status: ConnectionStatus) => {
    set({ 
      connectionStatus: status,
      isConnected: status === 'connected'
    })
  },

  toggleSidebar: () => {
    set((state) => ({ isSidebarOpen: !state.isSidebarOpen }))
  },
}))
