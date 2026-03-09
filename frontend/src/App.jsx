import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import DashboardLayout from './layouts/DashboardLayout'
import AuthLayout from './layouts/AuthLayout'
import ErrorBoundary from './components/ErrorBoundary'

// Auth pages – not lazy-loaded (needed immediately)
import Landing from './pages/LandingPage'
import Login from './pages/LoginPage'
import Signup from './pages/SignupPage'

// App pages – lazy-loaded for faster initial bundle
const Dashboard = lazy(() => import('./pages/DashboardPage'))
const Projects  = lazy(() => import('./pages/ProjectsPage'))
const Commits   = lazy(() => import('./pages/CommitAnalysisPage'))
const Analytics = lazy(() => import('./pages/AnalyticsPage'))
const Predict   = lazy(() => import('./pages/PredictPage'))
const Logs      = lazy(() => import('./pages/LogAnalyzerPage'))
const Profile   = lazy(() => import('./pages/ProfilePage'))

function PageLoader() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: '#388bfd', borderTopColor: 'transparent' }} />
    </div>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
      <Routes>
        {/* Marketing */}
        <Route path="/" element={<Landing />} />

        {/* Auth pages — centered card layout */}
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
        </Route>

        {/* Protected app pages — sidebar + topbar layout */}
        <Route element={<DashboardLayout />}>
          <Route path="/dashboard" element={<Suspense fallback={<PageLoader />}><Dashboard /></Suspense>} />
          <Route path="/projects"  element={<Suspense fallback={<PageLoader />}><Projects /></Suspense>} />
          <Route path="/commits"   element={<Suspense fallback={<PageLoader />}><Commits /></Suspense>} />
          <Route path="/analytics" element={<Suspense fallback={<PageLoader />}><Analytics /></Suspense>} />
          <Route path="/predict"   element={<Suspense fallback={<PageLoader />}><Predict /></Suspense>} />
          <Route path="/logs"      element={<Suspense fallback={<PageLoader />}><Logs /></Suspense>} />
          <Route path="/profile"   element={<Suspense fallback={<PageLoader />}><Profile /></Suspense>} />
        </Route>

        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </ErrorBoundary>
  )
}
