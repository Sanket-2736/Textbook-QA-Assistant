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
      return
    }

    setUploading(true)
    setError('')
    setUploadProgress('Uploading...')

    try {
      const formData = new FormData()
      formData.append('file', file)

      setUploadProgress('Ingesting into Pinecone...')
      const result = await api.postForm('/api/upload', formData)

      setUploadProgress('Ready!')
      setTimeout(() => setUploadProgress(''), 2000)
      onTextbookUploaded(result)
    } catch (err) {
      setError(err.message)
      setUploadProgress('')
    } finally {
      setUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleDelete = async (textbookId) => {
    if (!confirm('Delete this textbook and all associated chats? This cannot be undone.')) return

    try {
      await api.delete(`/api/textbooks/${textbookId}`)
      onTextbookDeleted(textbookId)
    } catch (err) {
      setError(err.message)
    }
  }

  const formatDate = (dateStr) => {
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    } catch {
      return 'Unknown'
    }
  }

  return (
    <div className="w-72 bg-white border-r border-gray-200 flex flex-col overflow-hidden shadow-sm">
      {/* Upload Section */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-sm font-semibold text-gray-900 mb-3">My Textbooks</h2>
        {error && (
          <div className="mb-3 p-2 bg-red-100 border border-red-300 rounded text-xs text-red-700">
            {error}
          </div>
        )}
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="w-full btn-primary text-sm flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span>+</span>
          {uploading ? 'Uploading...' : 'Upload PDF'}
        </button>
        {uploadProgress && (
          <p className="text-xs text-primary-600 mt-2 text-center">{uploadProgress}</p>
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
          <div className="p-4 text-center">
            <p className="text-sm text-gray-500">No textbooks yet</p>
            <p className="text-xs text-gray-400 mt-1">Upload a PDF to get started</p>
          </div>
        ) : (
          <ul className="p-2 space-y-2">
            {textbooks.map((textbook) => (
              <li key={textbook.id} className="group">
                <button
                  onClick={() => onSelectTextbook(textbook)}
                  className={`w-full text-left px-3 py-2 rounded-lg transition-colors text-sm ${
                    activeTextbook?.id === textbook.id
                      ? 'bg-primary-100 text-primary-900'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <div className="truncate font-medium">{textbook.filename}</div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    {textbook.page_count} pages • {formatDate(textbook.uploaded_at)}
                  </div>
                </button>
                {activeTextbook?.id === textbook.id && (
                  <button
                    onClick={() => handleDelete(textbook.id)}
                    className="ml-3 mt-1 text-xs text-red-600 hover:text-red-700 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    Delete
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-gray-200 bg-gray-50 text-xs text-gray-500">
        <p>📚 {textbooks.length} textbook{textbooks.length !== 1 ? 's' : ''}</p>
      </div>
    </div>
  )
}
