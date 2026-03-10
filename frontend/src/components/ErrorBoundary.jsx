import { Component } from 'react'
import { AlertTriangle } from 'lucide-react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, message: '' }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, message: error?.message ?? 'An unexpected error occurred' }
  }

  componentDidCatch(error, info) {
    // In production you'd send this to Sentry / Datadog
    console.error('[ErrorBoundary]', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-screen p-8 text-center bg-slate-50">
          <div className="p-4 rounded-2xl mb-6 bg-red-50 relative">
            <div className="absolute inset-0 bg-red-500 opacity-20 blur-xl rounded-full" />
            <AlertTriangle size={40} className="text-red-500 relative z-10" />
          </div>
          <h1 className="text-3xl font-bold mb-3 text-slate-900 tracking-tight">Something went wrong</h1>
          <p className="text-base max-w-md mb-8 text-slate-600 leading-relaxed">{this.state.message}</p>
          <button
            type="button"
            onClick={() => { this.setState({ hasError: false, message: '' }); window.location.href = '/dashboard' }}
            className="px-6 py-3 rounded-xl text-sm font-bold bg-indigo-600 text-white shadow-md hover:bg-indigo-700 hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200"
          >
            Back to Dashboard
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
