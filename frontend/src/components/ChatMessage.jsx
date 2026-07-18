import React, { useState } from 'react'

export default function ChatMessage({ message }) {
  const [showSources, setShowSources] = useState(false)
  const [showQuery, setShowQuery] = useState(false)

  const isUser = message.role === 'user'
  const isError = message.error

  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {/* Avatar */}
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-indigo-600 flex items-center justify-center text-white font-bold text-sm">
          AI
        </div>
      )}

      {/* Message Content */}
      <div
        className={`max-w-2xl ${
          isUser
            ? 'bg-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-2'
            : isError
            ? 'bg-red-50 border-l-4 border-red-500 rounded-lg px-4 py-3 text-red-700'
            : 'bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-3 text-gray-900'
        }`}
      >
        {/* Main message text */}
        <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
          {message.content}
        </p>

        {/* Sources Section */}
        {!isUser && !isError && message.sources && message.sources.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-300">
            <button
              onClick={() => setShowSources(!showSources)}
              className="text-xs font-semibold text-blue-700 hover:text-blue-800 flex items-center gap-1.5 transition"
            >
              <span className={`transform transition ${showSources ? 'rotate-90' : ''}`}>
                ▶
              </span>
              📎 {message.sources.length} {message.sources.length === 1 ? 'source' : 'sources'}
            </button>

            {showSources && (
              <div className="mt-3 space-y-2">
                {message.sources.map((source, idx) => (
                  <div
                    key={idx}
                    className="bg-white bg-opacity-60 rounded-lg p-3 border border-gray-200 hover:border-blue-300 hover:shadow-sm transition"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <div className="text-xs font-semibold text-gray-700">
                          {source.section ? (
                            <>
                              📖 <span className="text-blue-600">{source.section}</span>
                            </>
                          ) : (
                            '📄'
                          )}
                          {' '}Page {source.page}
                        </div>
                        <p className="text-xs text-gray-600 mt-1.5 line-clamp-3 leading-relaxed">
                          {source.text}
                        </p>
                      </div>
                      <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded font-medium flex-shrink-0">
                        p.{source.page}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Query Condensation Debug Info */}
        {!isUser && message.standalone_question && (
          <div className="mt-2 pt-2 border-t border-gray-200">
            <button
              onClick={() => setShowQuery(!showQuery)}
              className="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1 transition"
            >
              <span className={`transform transition ${showQuery ? 'rotate-90' : ''}`}>
                ▶
              </span>
              Show search query
            </button>
            {showQuery && (
              <p className="text-xs text-gray-600 italic mt-1.5 bg-gray-50 p-2 rounded">
                <span className="font-medium">🔍 Search query:</span>{' '}
                {message.standalone_question}
              </p>
            )}
          </div>
        )}
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-gray-400 to-gray-600 flex items-center justify center text-white font-bold text-sm">
          👤
        </div>
      )}
    </div>
  )
}
