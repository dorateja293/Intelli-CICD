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
        <div className="flex flex-col items-center justify-center min-h-screen p-8 text-center" style={{ background: '#0D1117' }}>
          <div className="p-4 rounded-xl mb-4" style={{ background: '#3d1a1a' }}>
            <AlertTriangle size={32} style={{ color: '#f85149' }} />
          </div>
          <h1 className="text-xl font-bold mb-2" style={{ color: '#E6EDF3' }}>Something went wrong</h1>
          <p className="text-sm max-w-sm mb-6" style={{ color: '#8B949E' }}>{this.state.message}</p>
          <button
            type="button"
            onClick={() => { this.setState({ hasError: false, message: '' }); window.location.href = '/dashboard' }}
            className="px-5 py-2 rounded-lg text-sm font-medium"
            style={{ background: '#388bfd', color: '#fff' }}
          >
            Back to Dashboard
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
