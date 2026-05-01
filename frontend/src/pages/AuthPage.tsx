import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plane, Loader2, AlertCircle } from 'lucide-react'
import { login, register } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import { cn } from '@/lib/utils'

export default function AuthPage() {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { setToken } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (mode === 'register') {
        await register(email, password)
        // auto-login after register
      }
      await login(email, password)
      setToken(localStorage.getItem('token'))
      navigate('/chat')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4"
         style={{ background: 'linear-gradient(135deg, #0f1117 0%, #0c1929 50%, #0f1117 100%)' }}>

      {/* Background glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full opacity-10"
             style={{ background: 'radial-gradient(circle, #0ea5e9 0%, transparent 70%)' }} />
      </div>

      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-4"
               style={{ background: 'linear-gradient(135deg, #0ea5e9, #0369a1)' }}>
            <Plane className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">Smart Travel Planner</h1>
          <p className="text-slate-400 mt-1 text-sm">AI-powered trip recommendations</p>
        </div>

        {/* Card */}
        <div className="rounded-2xl border border-slate-700/50 p-8"
             style={{ background: '#161b25' }}>

          {/* Tabs */}
          <div className="flex rounded-xl p-1 mb-6" style={{ background: '#0f1117' }}>
            {(['login', 'register'] as const).map(m => (
              <button key={m} onClick={() => { setMode(m); setError('') }}
                className={cn(
                  'flex-1 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                  mode === m
                    ? 'bg-brand-500 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                )}>
                {m === 'login' ? 'Sign In' : 'Sign Up'}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Email</label>
              <input
                type="email" required value={email} onChange={e => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full px-4 py-2.5 rounded-xl text-sm text-white placeholder-slate-500
                           border border-slate-700 outline-none transition-all duration-200
                           focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
                style={{ background: '#0f1117' }}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Password</label>
              <input
                type="password" required value={password} onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-4 py-2.5 rounded-xl text-sm text-white placeholder-slate-500
                           border border-slate-700 outline-none transition-all duration-200
                           focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
                style={{ background: '#0f1117' }}
              />
            </div>

            {error && (
              <div className="flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm text-red-400
                              bg-red-950/40 border border-red-800/50">
                <AlertCircle className="w-4 h-4 shrink-0" />
                {error}
              </div>
            )}

            <button type="submit" disabled={loading}
              className="w-full py-2.5 rounded-xl font-medium text-white text-sm
                         transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed
                         flex items-center justify-center gap-2"
              style={{ background: loading ? '#0369a1' : 'linear-gradient(135deg, #0ea5e9, #0369a1)' }}>
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              {mode === 'login' ? 'Sign In' : 'Create Account'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
