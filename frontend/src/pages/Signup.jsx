import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

export default function Signup() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { signup } = useAuth()

  const validateForm = () => {
    const errors = {}

    if (!email.trim()) {
      errors.email = 'Email is required'
    } else if (!validateEmail(email)) {
      errors.email = 'Please enter a valid email address'
    }

    if (!password.trim()) {
      errors.password = 'Password is required'
    } else if (password.length < 6) {
      errors.password = 'Password must be at least 6 characters'
    }

    if (!confirmPassword.trim()) {
      errors.confirmPassword = 'Please confirm your password'
    } else if (password !== confirmPassword) {
      errors.confirmPassword = 'Passwords do not match'
    }

    setFieldErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!validateForm()) {
      return
    }

    setLoading(true)

    try {
      await signup(email, password)
      navigate('/')
    } catch (err) {
      const message = err.message
      if (message.includes('already registered')) {
        setError('❌ Email is already registered. Please log in instead.')
      } else if (message.includes('validation') || message.includes('422')) {
        setError('❌ Email format is invalid')
      } else {
        setError(`❌ ${message}`)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          {/* Header */}
          <div className="p-8 text-center bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
            <div className="text-5xl mb-3">📚</div>
            <h1 className="text-3xl font-bold mb-1">TextBook AI</h1>
            <p className="text-blue-100 text-sm">Create Your Account</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-8 space-y-5">
            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 font-medium">
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value)
                  if (fieldErrors.email) setFieldErrors({ ...fieldErrors, email: '' })
                }}
                className={`w-full px-4 py-2.5 border rounded-lg focus:outline-none focus:ring-2 transition ${
                  fieldErrors.email
                    ? 'border-red-300 focus:ring-red-500'
                    : 'border-gray-300 focus:ring-blue-500'
                } disabled:bg-gray-100 disabled:text-gray-500`}
                placeholder="you@example.com"
                disabled={loading}
              />
              {fieldErrors.email && (
                <p className="text-red-600 text-xs mt-1.5 font-medium">⚠️ {fieldErrors.email}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value)
                  if (fieldErrors.password) setFieldErrors({ ...fieldErrors, password: '' })
                }}
                className={`w-full px-4 py-2.5 border rounded-lg focus:outline-none focus:ring-2 transition ${
                  fieldErrors.password
                    ? 'border-red-300 focus:ring-red-500'
                    : 'border-gray-300 focus:ring-blue-500'
                } disabled:bg-gray-100 disabled:text-gray-500`}
                placeholder="••••••••"
                disabled={loading}
              />
              {fieldErrors.password && (
                <p className="text-red-600 text-xs mt-1.5 font-medium">⚠️ {fieldErrors.password}</p>
              )}
              <p className="text-xs text-gray-500 mt-1">At least 6 characters</p>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Confirm Password
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => {
                  setConfirmPassword(e.target.value)
                  if (fieldErrors.confirmPassword)
                    setFieldErrors({ ...fieldErrors, confirmPassword: '' })
                }}
                className={`w-full px-4 py-2.5 border rounded-lg focus:outline-none focus:ring-2 transition ${
                  fieldErrors.confirmPassword
                    ? 'border-red-300 focus:ring-red-500'
                    : 'border-gray-300 focus:ring-blue-500'
                } disabled:bg-gray-100 disabled:text-gray-500`}
                placeholder="••••••••"
                disabled={loading}
              />
              {fieldErrors.confirmPassword && (
                <p className="text-red-600 text-xs mt-1.5 font-medium">⚠️ {fieldErrors.confirmPassword}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold rounded-lg hover:shadow-lg disabled:opacity-60 disabled:cursor-not-allowed transition duration-200 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <span className="inline-block animate-spin">⟳</span>
                  <span>Creating account...</span>
                </>
              ) : (
                <>
                  <span>✨</span>
                  <span>Create Account</span>
                </>
              )}
            </button>
          </form>

          {/* Footer */}
          <div className="px-8 py-6 bg-gray-50 border-t border-gray-200 text-center">
            <p className="text-gray-700 text-sm">
              Already have an account?{' '}
              <Link to="/login" className="text-blue-600 hover:text-blue-700 font-semibold">
                Sign in
              </Link>
            </p>
          </div>
        </div>

        {/* Additional Info */}
        <div className="mt-8 text-center text-gray-600 text-sm">
          <p>🔒 Your data is secure and encrypted</p>
        </div>
      </div>
    </div>
  )
}
