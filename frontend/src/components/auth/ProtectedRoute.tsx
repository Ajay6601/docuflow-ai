import React, { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
// import { useAuthStore } from '../../store/authStore'
import { Loader2 } from 'lucide-react'
import { useAuthStore } from '../../store/authSore'
interface ProtectedRouteProps {
  children: React.ReactNode
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, loadUser, user } = useAuthStore()
  const [loading, setLoading] = useState(true)
  const [shouldRedirect, setShouldRedirect] = useState(false)

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token')
      
      if (!token) {
        setLoading(false)
        setShouldRedirect(true)
        return
      }

      if (isAuthenticated && !user) {
        try {
          await loadUser()
        } catch (error) {
          console.error('Failed to load user:', error)
          setShouldRedirect(true)
        }
      }
      
      setLoading(false)
    }

    checkAuth()
  }, [isAuthenticated, user, loadUser])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto mb-4" />
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (shouldRedirect || !isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}