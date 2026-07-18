import React, { useState, useEffect, useRef } from 'react'
import ChatMessage from './ChatMessage'
import { useApi } from '../lib/api'

export default function ChatPanel({
  activeTextbook,
  activeSession,
  onSessionCreated,
}) {
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const messagesEndRef = useRef(null)
  const api = useApi()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Fetch messages from session when session changes
  useEffect(() => {
    if (activeSession?.id) {
      loadSessionMessages()
    } else {
      setMessages([])
    }
  }, [activeSession?.id])

  const loadSessionMessages = async () => {
    try {
      const messageList = await api.get(`/sessions/${activeSession.id}/messages`)
      setMessages(messageList || [])
    } catch (err) {
      console.error('Failed to load messages:', err)
      setMessages([])
    }
  }

  const handleAskQuestion = async (e) => {
    e.preventDefault()
    if (!question.trim() || !activeTextbook || loading) return

    const userMessage = {
      role: 'user',
      content: question,
    }

    setMessages((prev) => [...prev, userMessage])
    setQuestion('')
    setLoading(true)
    setError('')

    try {
      // Call the synchronous /ask endpoint
      const response = await api.post('/ask', {
        question,
        textbook_id: activeTextbook.id,
        session_id: activeSession?.id || null,
        top_k: 4,
      })

      // Create assistant message from response
      const assistantMessage = {
        id: Date.now(),
        role: 'assistant',
        content: response.answer,
        sources: response.sources || [],
        standalone_question: response.standalone_question,
        created_at: new Date().toISOString(),
      }

      setMessages((prev) => [...prev, assistantMessage])

      // If this was a new session, notify parent
      if (!activeSession && response.session_id) {
        onSessionCreated(response.session_id, question)
      }
    } catch (err) {
      setError(err.message || 'Failed to get answer')
      const errorMessage = {
        role: 'assistant',
        content: `❌ Error: ${err.message || 'Failed to get answer. Please try again.'}`,
        error: true,
        created_at: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  if (!activeTextbook) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-2xl mb-2">📚</p>
          <p className="text-lg text-gray-700 font-medium">Select a textbook to begin</p>
          <p className="text-sm text-gray-500 mt-2">Upload or choose from the left sidebar</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 shadow-sm">
        <h2 className="font-semibold text-gray-900 truncate">{activeTextbook.filename}</h2>
        <p className="text-sm text-gray-600 mt-1">
          {activeSession
            ? `📖 Session: ${activeSession.title || 'Untitled'}`
            : '✨ Start a new conversation'}
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center text-gray-600">
              <p className="text-xl font-medium mb-2">💬 Ask a question</p>
              <p className="text-sm text-gray-500">
                {activeSession
                  ? 'Continue the conversation or ask something new'
                  : 'Start a new chat about this textbook'}
              </p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, idx) => (
              <ChatMessage key={idx} message={msg} />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Error Alert */}
      {error && (
        <div className="px-6 py-3 bg-red-50 border-t border-red-200 text-sm text-red-700 font-medium">
          ⚠️ {error}
        </div>
      )}

      {/* Input Area */}
      <form
        onSubmit={handleAskQuestion}
        className="border-t border-gray-200 p-4 bg-white"
      >
        <div className="flex gap-3">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={
              activeTextbook
                ? 'Ask a question about this textbook...'
                : 'Select a textbook to begin'
            }
            disabled={loading || !activeTextbook}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed transition"
          />
          <button
            type="submit"
            disabled={loading || !question.trim() || !activeTextbook}
            className="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition duration-200 flex items-center gap-2"
          >
            {loading ? (
              <>
                <span className="inline-block animate-spin">⟳</span>
                <span className="hidden sm:inline">Thinking...</span>
              </>
            ) : (
              '🚀 Send'
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
