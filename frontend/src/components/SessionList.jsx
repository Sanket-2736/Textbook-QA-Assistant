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
  }, [activeTextbook])

  const loadSessions = async () => {
    if (!activeTextbook) return
    try {
      setLoading(true)
      const data = await api.get(`/api/sessions?textbook_id=${activeTextbook.id}`)
      setSessions(data || [])
    } catch (err) {
      console.error('Failed to load sessions:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSessionSelect = async (session) => {
    try {
      const messages = await api.get(`/api/sessions/${session.id}/messages`)
      onSelectSession({ ...session, messages })
    } catch (err) {
      console.error('Failed to load session messages:', err)
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
    <div className="w-64 bg-gray-50 border-r border-gray-200 flex flex-col overflow-hidden">
      {/* New Chat Button */}
      <div className="p-4 border-b border-gray-200">
        <button
          onClick={onNewChat}
          className="w-full btn-secondary text-sm flex items-center justify-center gap-2"
        >
          <span>+</span>
          New Chat
        </button>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4 text-center">
            <p className="text-xs text-gray-500">Loading chats...</p>
          </div>
        ) : sessions.length === 0 ? (
          <div className="p-4 text-center">
            <p className="text-sm text-gray-500">No chats yet</p>
            <p className="text-xs text-gray-400 mt-1">Start a conversation</p>
          </div>
        ) : (
          <ul className="p-2 space-y-1">
            {sessions.map((session) => (
              <li key={session.id}>
                <button
                  onClick={() => handleSessionSelect(session)}
                  className={`w-full text-left px-3 py-2 rounded-lg transition-colors text-sm truncate ${
                    activeSession?.id === session.id
                      ? 'bg-white text-primary-900 font-medium shadow-sm'
                      : 'text-gray-700 hover:bg-white hover:shadow-sm'
                  }`}
                  title={session.title}
                >
                  {session.title || 'Untitled chat'}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-gray-200 bg-white text-xs text-gray-500 text-center">
        {sessions.length} chat{sessions.length !== 1 ? 's' : ''}
      </div>
    </div>
  )
}
