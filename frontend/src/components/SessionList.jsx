import React, { useState, useEffect } from 'react'
import { useApi } from '../lib/api'

export default function SessionList({
  activeTextbook,
  activeSession,
  onSelectSession,
  onNewChat,
}) {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(false)
  const api = useApi()

  useEffect(() => {
    if (activeTextbook) {
      loadSessions()
    } else {
      setSessions([])
    }
  }, [activeTextbook?.id])

  const loadSessions = async () => {
    if (!activeTextbook?.id) return
    try {
      setLoading(true)
      const data = await api.get(`/sessions?textbook_id=${activeTextbook.id}`)
      setSessions(data || [])
    } catch (err) {
      console.error('Failed to load sessions:', err)
      setSessions([])
    } finally {
      setLoading(false)
    }
  }

  const handleSessionSelect = async (session) => {
    try {
      const messages = await api.get(`/sessions/${session.id}/messages`)
      onSelectSession({ ...session, messages })
    } catch (err) {
      console.error('Failed to load session messages:', err)
      // Still select the session even if we can't load messages
      onSelectSession(session)
    }
  }

  const formatDate = (dateStr) => {
    try {
      const date = new Date(dateStr)
      const today = new Date()
      const isToday = date.toDateString() === today.toDateString()
      return isToday ? date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }) : date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    } catch {
      return ''
    }
  }

  if (!activeTextbook) {
    return (
      <div className="w-64 bg-gray-50 border-r border-gray-200 flex items-center justify-center">
        <p className="text-sm text-gray-500 text-center px-4">Select a textbook to view chats</p>
      </div>
    )
  }

  return (
    <div className="w-64 bg-white border-r border-gray-200 flex flex-col overflow-hidden">
      {/* New Chat Button */}
      <div className="p-4 border-b border-gray-200 bg-gradient-to-b from-blue-50 to-white">
        <button
          onClick={onNewChat}
          className="w-full px-4 py-2.5 bg-blue-600 text-white font-medium text-sm rounded-lg hover:bg-blue-700 transition duration-200 flex items-center justify-center gap-2"
        >
          <span>💬</span>
          <span>New Chat</span>
        </button>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-8 text-center text-gray-500">
            <div className="animate-spin inline-block">⟳</div>
            <p className="text-xs mt-2">Loading conversations...</p>
          </div>
        ) : sessions.length === 0 ? (
          <div className="p-8 text-center h-full flex items-center justify-center">
            <div>
              <p className="text-2xl mb-2">💭</p>
              <p className="text-sm font-medium text-gray-700">No conversations yet</p>
              <p className="text-xs text-gray-500 mt-1">Start a new chat</p>
            </div>
          </div>
        ) : (
          <ul className="p-2 space-y-1">
            {sessions.map((session) => (
              <li key={session.id}>
                <button
                  onClick={() => handleSessionSelect(session)}
                  className={`w-full text-left px-3 py-3 rounded-lg transition-all text-sm group ${
                    activeSession?.id === session.id
                      ? 'bg-blue-100 text-blue-900 shadow-sm border border-blue-200'
                      : 'text-gray-700 hover:bg-gray-100 border border-transparent'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">
                        {session.title || '📝 Untitled chat'}
                      </div>
                      {session.created_at && (
                        <div className="text-xs text-gray-500 mt-1">
                          {formatDate(session.created_at)}
                        </div>
                      )}
                    </div>
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Footer */}
      {sessions.length > 0 && (
        <div className="p-3 border-t border-gray-200 bg-gray-50 text-xs text-gray-600 font-medium text-center">
          🗂️ {sessions.length} conversation{sessions.length !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  )
}
