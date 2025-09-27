import React, { useState, useEffect } from 'react'
import ChatApp from './ChatApp'
import AuthPage from './components/AuthPage'
import { isAuthenticated, getCurrentUser, logoutUser } from './utils/auth'
import './index.css'

export default function App() {
  const [isAuth, setIsAuth] = useState(false)
  const [currentUser, setCurrentUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  // Check authentication status on app load
  useEffect(() => {
    const checkAuth = async () => {
      try {
        if (isAuthenticated()) {
          const user = getCurrentUser()
          if (user) {
            setCurrentUser(user)
            setIsAuth(true)
          }
        }
      } catch (error) {
        console.error('Auth check failed:', error)
      } finally {
        setIsLoading(false)
      }
    }

    checkAuth()
  }, [])

  const handleAuthSuccess = (user) => {
    setCurrentUser(user)
    setIsAuth(true)
  }

  const handleLogout = () => {
    logoutUser()
    setIsAuth(false)
    setCurrentUser(null)
  }

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading EdRoom...</p>
        </div>
      </div>
    )
  }

  // Show authentication page if not authenticated
  if (!isAuth) {
    return <AuthPage onAuthSuccess={handleAuthSuccess} />
  }

  // Show main chat app if authenticated
  return (
    <ChatApp 
      currentUser={currentUser} 
      onLogout={handleLogout}
    />
  )
}
