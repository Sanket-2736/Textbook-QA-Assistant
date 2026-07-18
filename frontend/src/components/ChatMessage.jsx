import React, { useState } from 'react'

export default function ChatMessage({ message }) {
  const [showSources, setShowSources] = useState(false)
  const [showStandaloneQuestion, setShowStandaloneQuestion] = useState(false)

  const isUser = message.role === 'user'
  const isError = message.error
  const isStreaming = message.isStreaming

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-2xl rounded-lg px-4 py-3 ${
          isUser
            ? 'bg-primary-600 text-white'
            : isError
            ? 'bg-red-100 text-red-900 border border-red-300'
            : 'bg-gray-100 text-gray-900'
        } ${isStreaming ? 'opacity-90' : ''}`}
      >
        <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
          {message.content}
          {isStreaming && <span className="animate-pulse">▌</span>}
        </p>

        {/* Sources */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-300">
            <button
              onClick={() => setShowSources(!showSources)}
              className="text-xs font-medium text-primary-700 hover:text-primary-800 flex items-center gap-1"
            >
              {showSources ? '▼' : '▶'} {message.sources.length} source
              {message.sources.length !== 1 ? 's' : ''}
            </button>

            {showSources && (
              <div className="mt-2 space-y-2">
                {message.sources.map((source, idx) => (
                  <div
                    key={idx}
                    className="text-xs bg-white bg-opacity-50 rounded p-2 border border-gray-300"
                  >
                    <div className="font-semibold text-gray-700">
                      {source.section ? `${source.section} ` : ''}
                      (Page {source.page})
                    </div>
                    <p className="text-gray-600 mt-1 line-clamp-2">
                      {source.text}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Debug: Standalone Question */}
        {!isUser && message.standalone_question && (
          <div className="mt-2 pt-2 border-t border-gray-300">
            <button
              onClick={() => setShowStandaloneQuestion(!showStandaloneQuestion)}
              className="text-xs text-gray-500 hover:text-gray-700 italic"
            >
              {showStandaloneQuestion ? '▼ Hide query' : '▶ Show query'}
            </button>
            {showStandaloneQuestion && (
              <p className="text-xs text-gray-500 italic mt-1">
                Condensed query: {message.standalone_question}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
