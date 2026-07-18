import React, { useState, useEffect, useRef } from 'react'
import ChatMessage from './ChatMessage'
import { useApi } from '../lib/api'
import { apiFetch } from '../lib/api'

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

  useEffect(() => {
    if (activeSession?.messages) {
      setMessages(activeSession.messages)
    } else {
      setMessages([])
    }
  }, [activeSession])

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
      // Stream the response from /ask/stream
      const streamResponse = await apiFetch('/api/ask/stream', {
        method: 'POST',
        body: JSON.stringify({
          question,
          textbook_id: activeTextbook.id,
          session_id: activeSession?.id || null,
        }),
      })

      let assistantContent = ''
      let assistantData = {
        sources: [],
        standalone_question: '',
        session_id: null,
      }

      const reader = streamResponse.body.getReader()
      const decoder = new TextDecoder()

      // Add empty assistant message to update in real-time
      const assistantMsgIdx = messages.length + 1
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: '',
          sources: [],
          standalone_question: '',
          isStreaming: true,
        },
      ])

      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')

        // Keep the last incomplete line in the buffer
        buffer = lines[lines.length - 1]

        for (let i = 0; i < lines.length - 1; i++) {
          const line = lines[i]

          if (line.startsWith('data: ')) {
            try {
              const jsonStr = line.slice(6)
              const chunk = JSON.parse(jsonStr)

              if (chunk.token) {
                // Accumulate token
                assistantContent += chunk.token

                // Update message in real-time
                setMessages((prev) => {
                  const updated = [...prev]
                  updated[assistantMsgIdx] = {
                    ...updated[assistantMsgIdx],
                    content: assistantContent,
                    isStreaming: true,
                  }
                  return updated
                })
              }

              if (chunk.sources) {
                assistantData.sources = chunk.sources
              }
              if (chunk.standalone_question) {
                assistantData.standalone_question = chunk.standalone_question
              }
              if (chunk.session_id) {
                assistantData.session_id = chunk.session_id
                // Notify parent of new session
                if (!activeSession) {
                  onSessionCreated(chunk.session_id, question)
                }
              }
            } catch (err) {
              // Skip invalid JSON
            }
          }
        }
      }

      // Finalize the message
      setMessages((prev) => {
        const updated = [...prev]
        updated[assistantMsgIdx] = {
          role: 'assistant',
          content: assistantContent,
          sources: assistantData.sources,
          standalone_question: assistantData.standalone_question,
          isStreaming: false,
        }
        return updated
      })
    } catch (err) {
      setError(err.message)
      const errorMessage = {
        role: 'assistant',
        content: `Error: ${err.message}`,
        error: true,
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
          <p className="text-lg text-gray-600">📚 Select a textbook to begin</p>
          <p className="text-sm text-gray-400 mt-2">Upload or choose from the left</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 p-4 bg-gradient-to-r from-primary-50 to-blue-50">
        <h2 className="font-semibold text-gray-900">{activeTextbook.filename}</h2>
        <p className="text-sm text-gray-600 mt-1">
          {activeSession
            ? `Session: ${activeSession.title || 'Untitled'}`
            : 'Start a new conversation'}
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center text-gray-500">
              <p className="text-lg font-medium">Ask a question</p>
              <p className="text-sm mt-2">
                {activeSession
                  ? 'Continue the conversation'
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
        <div className="px-4 py-2 bg-red-100 border-t border-red-300 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Input */}
      <form
        onSubmit={handleAskQuestion}
        className="border-t border-gray-200 p-4 bg-gray-50"
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
            className="input-field flex-1 disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={loading || !question.trim() || !activeTextbook}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed px-6"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <span className="animate-spin inline-block">⟳</span>
                <span className="hidden sm:inline">Streaming...</span>
              </span>
            ) : (
              'Send'
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
