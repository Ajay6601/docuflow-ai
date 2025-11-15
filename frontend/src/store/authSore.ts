import { create } from 'zustand'
import { User } from '../types/user'
import { authApi } from '../services/api'

interface AuthStore {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  
  // Actions
  login: (username: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string, fullName?: string) => Promise<void>
  logout: () => void
  loadUser: () => Promise<void>
  setUser: (user: User | null) => void
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  token: localStorage.getItem('access_token'),
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoading: false,

  login: async (username: string, password: string) => {
    set({ isLoading: true })
    try {
      const response = await authApi.login(username, password)
      
      localStorage.setItem('access_token', response.access_token)
      
      // Get user data
      const user = await authApi.getCurrentUser()
      
      set({
        token: response.access_token,
        user,
        isAuthenticated: true,
        isLoading: false,
      })
    } catch (error) {
      set({ isLoading: false })
      console.error('Login error:', error)
      throw error
    }
  },

  register: async (email: string, username: string, password: string, fullName?: string) => {
    set({ isLoading: true })
    try {
      await authApi.register(email, username, password, fullName)
      
      // Auto-login after registration
      await useAuthStore.getState().login(username, password)
    } catch (error) {
      set({ isLoading: false })
      console.error('Registration error:', error)
      throw error
    }
  },

  logout: () => {
    try {
      authApi.logout()
    } catch (error) {
      console.error('Logout error:', error)
    }
    
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    
    set({
      user: null,
      token: null,
      isAuthenticated: false,
    })
  },

  loadUser: async () => {
    const token = localStorage.getItem('access_token')
    
    if (!token) {
      set({ user: null, isAuthenticated: false, token: null })
      return
    }

    try {
      const user = await authApi.getCurrentUser()
      set({ user, isAuthenticated: true, token })
    } catch (error) {
      console.error('Load user error:', error)
      // Token is invalid
      localStorage.removeItem('access_token')
      set({ user: null, token: null, isAuthenticated: false })
      throw error
    }
  },

  setUser: (user: User | null) => {
    set({ user })
  },
}))