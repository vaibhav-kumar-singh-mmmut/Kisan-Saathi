import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import LoginPage from './components/LoginPage'
import SignupPage from './components/SignupPage'
import FarmerShell from './components/FarmerShell'
import OfficerDashboard from './components/OfficerDashboard'

function Router() {
  const { user, isLoading } = useAuth()
  const [authView, setAuthView] = useState<'login' | 'signup'>('login')
  useTranslation()

  if (isLoading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg)', color: 'var(--text)' }}>
        <p>Loading...</p>
      </div>
    )
  }

  if (!user) {
    if (authView === 'signup') {
      return <SignupPage onNavigateToLogin={() => setAuthView('login')} />
    }
    return <LoginPage onNavigateToSignup={() => setAuthView('signup')} />
  }

  if (user.user_type?.toLowerCase() === 'farmer' || user.role?.toLowerCase() === 'farmer') {
    return (
      <div className="shell-container">
        <FarmerShell />
      </div>
    )
  }

  return <OfficerDashboard />
}

export default function App() {
  return (
    <AuthProvider>
      <Router />
    </AuthProvider>
  )
}
