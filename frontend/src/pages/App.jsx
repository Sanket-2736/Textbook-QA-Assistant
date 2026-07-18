import React, { useState, useEffect } from 'react'
import Header from '../components/Header'
import TextbookList from '../components/TextbookList'
import SessionList from '../components/SessionList'
import ChatPanel from '../components/ChatPanel'
import { useApi } from '../lib/api'

export default function AppPage() {
  const [activeTextbook, setActiveTextbook] = useState(null)
  const [activeSession, setActiveSession] = useState(null)
  const [textbooks, setTextbooks] = useState([])
  const [loading, setLoading] = useState(true)
  const api = useApi()

  useEffect(() => {
    loadTextbooks()
  }, [])

  const loadTextbooks = async () => {
    try {
      const list = await api.get('/textbooks')
      setTextbooks(list || [])
      if (list?.length > 0) {
        setActiveTextbook(list[0])
      }
    } catch (error) {
      console.error('Failed to load textbooks:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleTextbookSelect = (textbook) => {
    setActiveTextbook(textbook)
    setActiveSession(null)
  }

  const handleTextbookUploaded = (newTextbook) => {
    setTextbooks([...textbooks, newTextbook])
    setActiveTextbook(newTextbook)
    setActiveSession(null)
  }

  const handleTextbookDeleted = (textbookId) => {
    const remaining = textbooks.filter((t) => t.id !== textbookId)
    setTextbooks(remaining)
    if (activeTextbook?.id === textbookId) {
      setActiveTextbook(remaining[0] || null)
      setActiveSession(null)
    }
  }

  const handleNewChat = () => {
    setActiveSession(null)
  }

  const handleSessionSelected = (session) => {
    setActiveSession(session)
  }

  const handleSessionCreated = async (sessionId, firstQuestion) => {
    // Refresh sessions list when a new session is created
    try {
      if (activeTextbook?.id) {
        const sessions = await api.get(`/sessions?textbook_id=${activeTextbook.id}`)
        const newSession = sessions.find((s) => s.id === sessionId)
        if (newSession) {
          setActiveSession(newSession)
        }
      }
    } catch (err) {
      console.error('Failed to refresh sessions:', err)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4 mx-auto"></div>
          <p className="text-gray-700 font-medium">Loading textbooks...</p>
          <p className="text-sm text-gray-500 mt-1">Please wait</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <TextbookList
          textbooks={textbooks}
          activeTextbook={activeTextbook}
          onSelectTextbook={handleTextbookSelect}
          onTextbookUploaded={handleTextbookUploaded}
          onTextbookDeleted={handleTextbookDeleted}
        />
        <SessionList
          activeTextbook={activeTextbook}
          activeSession={activeSession}
          onSelectSession={handleSessionSelected}
          onNewChat={handleNewChat}
        />
        <ChatPanel
          activeTextbook={activeTextbook}
          activeSession={activeSession}
          onSessionCreated={handleSessionCreated}
        />
      </div>
    </div>
  )
}
