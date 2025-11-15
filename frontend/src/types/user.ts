export interface User {
  id: number
  email: string
  username: string
  full_name?: string
  role: 'admin' | 'user' | 'viewer'
  is_active: boolean
  is_verified: boolean
  created_at: string
  last_login?: string
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface RegisterData {
  email: string
  username: string
  password: string
  full_name?: string
}

export interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
}
