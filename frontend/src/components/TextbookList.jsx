import React, { useState, useRef } from 'react'
import { useApi } from '../lib/api'

export default function TextbookList({
  textbooks,
  activeTextbook,
  onSelectTextbook,
  onTextbookUploaded,
  onTextbookDeleted,
}) {
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState('')
  const [error, setError] = useState('')
  const fileInputRef = useRef(null)
  const api = useApi()

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Please select a PDF file')
      setTimeout(() => setError(''), 4000)
      return
    }

    setUploading(true)
    setError('')
    setUploadProgress('Uploading file...')

    try {
      const formData = new FormData()
      formData.append('file', file)

      setUploadProgress('Extracting text and embedding...')
      const result = await api.postForm('/upload', formData)

      setUploadProgress('✅ Upload complete!')
      setTimeout(() => setUploadProgress(''), 2000)
      onTextbookUploaded(result)
    } catch (err) {
      setError(err.message || 'Upload failed')
      setUploadProgress('')
    } finally {
      setUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleDelete = async (textbookId, event) => {
    event.stopPropagation()
    if (!confirm('Delete this textbook and all associated chats? This cannot be undone.')) return

    try {
      await api.delete(`/textbooks/${textbookId}`)
      onTextbookDeleted(textbookId)
    } catch (err) {
      setError(err.message || 'Failed to delete textbook')
    }
  }

  const formatDate = (dateStr) => {
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      })
    } catch {
      return 'Unknown'
    }
  }

  return (
    <div className="w-72 bg-white border-r border-gray-200 flex flex-col overflow-hidden shadow-sm">
      {/* Upload Section */}
      <div className="p-4 border-b border-gray-200 bg-gradient-to-b from-gray-50 to-white">
        <h2 className="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
          📚 My Textbooks
        </h2>
        {error && (
          <div className="mb-3 p-2.5 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 font-medium">
            ⚠️ {error}
          </div>
        )}
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="w-full px-4 py-2.5 bg-blue-600 text-white font-medium text-sm rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition duration-200 flex items-center justify-center gap-2"
        >
          {uploading ? (
            <>
              <span className="inline-block animate-spin">⟳</span>
              <span>Uploading...</span>
            </>
          ) : (
            <>
              <span>📤</span>
              <span>Upload PDF</span>
            </>
          )}
        </button>
        {uploadProgress && (
          <p className="text-xs text-blue-600 mt-2.5 text-center font-medium">{uploadProgress}</p>
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileSelect}
          disabled={uploading}
          className="hidden"
        />
      </div>

      {/* Textbooks List */}
      <div className="flex-1 overflow-y-auto">
        {textbooks.length === 0 ? (
          <div className="p-6 text-center h-full flex items-center justify-center">
            <div>
              <p className="text-2xl mb-2">📑</p>
              <p className="text-sm font-medium text-gray-700">No textbooks yet</p>
              <p className="text-xs text-gray-500 mt-1">Upload a PDF to get started</p>
            </div>
          </div>
        ) : (
          <ul className="p-2 space-y-1">
            {textbooks.map((textbook) => (
              <li key={textbook.id} className="group">
                <button
                  onClick={() => onSelectTextbook(textbook)}
                  className={`w-full text-left px-3 py-3 rounded-lg transition-all text-sm ${
                    activeTextbook?.id === textbook.id
                      ? 'bg-blue-100 text-blue-900 shadow-sm border border-blue-200'
                      : 'text-gray-700 hover:bg-gray-100 border border-transparent'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <span className="text-lg flex-shrink-0 mt-0.5">📖</span>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{textbook.filename}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        {textbook.page_count} pages {textbook.uploaded_at && `• ${formatDate(textbook.uploaded_at)}`}
                      </div>
                    </div>
                  </div>
                </button>
                {activeTextbook?.id === textbook.id && (
                  <button
                    onClick={(e) => handleDelete(textbook.id, e)}
                    className="ml-8 mt-1 px-2 py-1 text-xs text-red-600 hover:text-red-700 hover:bg-red-50 rounded transition-colors opacity-0 group-hover:opacity-100"
                  >
                    🗑️ Delete
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Footer Stats */}
      {textbooks.length > 0 && (
        <div className="p-4 border-t border-gray-200 bg-gray-50 text-xs text-gray-600 font-medium">
          <p>� {textbooks.length} textbook{textbooks.length !== 1 ? 's' : ''}</p>
        </div>
      )}
    </div>
  )
}
