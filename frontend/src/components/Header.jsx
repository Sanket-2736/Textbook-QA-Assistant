import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Header() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
        {/* Logo & Title */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-md">
            <span className="text-white font-bold text-xl">📚</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">TextBook AI</h1>
            <p className="text-xs text-gray-500 font-medium">Interactive Q&A powered by Cerebras</p>
          </div>
        </div>

        {/* User Section */}
        {user && (
          <div className="flex items-center gap-6">
            <div className="text-right">
              <p className="text-sm font-medium text-gray-900">{user.email}</p>
              <p className="text-xs text-green-600 font-medium flex items-center gap-1 mt-0.5">
                <span className="w-2 h-2 bg-green-600 rounded-full inline-block"></span>
                Connected
              </p>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all duration-200 border border-transparent hover:border-gray-300"
            >
              🚪 Logout
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
