import { useState, useRef, useEffect, type KeyboardEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Send, Loader2, History, LogOut, Wrench, Plane, AlertCircle, Webhook
} from 'lucide-react'
import { chat } from '@/lib/api'
import type { ToolCallRecord } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import ChatMessage, { type Message } from '@/components/ChatMessage'
import ToolCallDrawer from '@/components/ToolCallDrawer'
import WebhookSettings from '@/components/WebhookSettings'

const SUGGESTIONS = [
  'Where should I go for adventure hiking in South America?',
  'Recommend a relaxing beach destination in Southeast Asia',
  'Best cultural city break in Europe under $1,500?',
  'Family-friendly destination with good weather in March',
]

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [toolCalls, setToolCalls] = useState<ToolCallRecord[]>([])
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [webhookOpen, setWebhookOpen] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const { logout } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function sendMessage(text: string) {
    if (!text.trim() || loading) return
    setError('')
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setInput('')
    setLoading(true)

    // Add streaming placeholder
    setMessages(prev => [...prev, { role: 'assistant', content: '' }])

    try {
      const res = await chat(text)
      setMessages(prev => [
        ...prev.slice(0, -1),
        { role: 'assistant', content: res.answer, usage: res.token_usage },
      ])
      // mock tool calls from last response — real ones come from history
      setToolCalls([])
    } catch (err: unknown) {
      setMessages(prev => prev.slice(0, -1))
      setError(err instanceof Error ? err.message : 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  function handleKey(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  function handleLogout() {
    logout()
    navigate('/auth')
  }

  const isEmpty = messages.length === 0

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: '#0f1117' }}>

      {/* Sidebar */}
      <aside className="flex flex-col w-56 shrink-0 border-r border-slate-800 py-4"
             style={{ background: '#161b25' }}>
        <div className="px-4 mb-6 flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl flex items-center justify-center"
               style={{ background: 'linear-gradient(135deg, #0ea5e9, #0369a1)' }}>
            <Plane className="w-4 h-4 text-white" />
          </div>
          <span className="font-semibold text-sm text-white">Travel Planner</span>
        </div>

        <div className="flex-1 px-2 space-y-1">
          <button className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm
                             text-white bg-brand-500/15 border border-brand-500/20">
            <Send className="w-4 h-4 text-brand-400" />
            <span>Chat</span>
          </button>
          <button onClick={() => navigate('/history')}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm
                       text-slate-400 hover:text-white hover:bg-slate-700/40 transition-colors">
            <History className="w-4 h-4" />
            <span>History</span>
          </button>
          <button onClick={() => setWebhookOpen(true)}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm
                       text-slate-400 hover:text-white hover:bg-slate-700/40 transition-colors">
            <Webhook className="w-4 h-4" />
            <span>Webhook</span>
          </button>
        </div>

        <div className="px-2 mt-4">
          <button onClick={handleLogout}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm
                       text-slate-400 hover:text-red-400 hover:bg-red-950/30 transition-colors">
            <LogOut className="w-4 h-4" />
            <span>Sign out</span>
          </button>
        </div>
      </aside>

      {/* Main chat */}
      <div className="flex flex-1 flex-col min-w-0">

        {/* Header */}
        <header className="flex items-center justify-between px-6 py-3 border-b border-slate-800 shrink-0">
          <h1 className="font-semibold text-white text-sm">Ask anything about your next trip</h1>
          <button
            onClick={() => setDrawerOpen(v => !v)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
                       text-slate-400 hover:text-white hover:bg-slate-700/50 border border-slate-700/50
                       transition-colors">
            <Wrench className="w-3.5 h-3.5" />
            Tool calls
          </button>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
          {isEmpty && (
            <div className="flex flex-col items-center justify-center h-full text-center gap-6 py-12">
              <div className="w-16 h-16 rounded-2xl flex items-center justify-center"
                   style={{ background: 'linear-gradient(135deg, #0ea5e9, #0369a1)' }}>
                <Plane className="w-8 h-8 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white mb-2">Plan your next adventure</h2>
                <p className="text-slate-400 text-sm">Ask me about destinations, weather, travel styles, and more.</p>
              </div>
              <div className="grid grid-cols-2 gap-2 w-full max-w-lg">
                {SUGGESTIONS.map(s => (
                  <button key={s} onClick={() => sendMessage(s)}
                    className="text-left px-4 py-3 rounded-xl text-xs text-slate-300
                               border border-slate-700/50 hover:border-brand-500/50
                               hover:bg-brand-500/5 transition-all duration-200"
                    style={{ background: '#161b25' }}>
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i}>
              {msg.role === 'assistant' && loading && i === messages.length - 1 && !msg.content ? (
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0"
                       style={{ background: 'linear-gradient(135deg, #0ea5e9, #0369a1)' }}>
                    <Loader2 className="w-4 h-4 text-white animate-spin" />
                  </div>
                  <div className="flex gap-1">
                    {[0, 1, 2].map(i => (
                      <div key={i} className="w-2 h-2 rounded-full bg-brand-500 animate-bounce"
                           style={{ animationDelay: `${i * 0.15}s` }} />
                    ))}
                  </div>
                </div>
              ) : (
                <ChatMessage msg={msg} />
              )}
            </div>
          ))}

          {error && (
            <div className="flex items-center gap-2 px-4 py-3 rounded-xl text-sm text-red-400
                            bg-red-950/40 border border-red-800/50">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="px-6 pb-6 shrink-0">
          <div className="flex items-end gap-3 px-4 py-3 rounded-2xl border border-slate-700/50
                          focus-within:border-brand-500/50 transition-colors"
               style={{ background: '#161b25' }}>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Where should I travel…"
              rows={1}
              disabled={loading}
              className="flex-1 bg-transparent text-sm text-white placeholder-slate-500
                         outline-none resize-none leading-relaxed max-h-32 overflow-y-auto"
              style={{ minHeight: '1.5rem' }}
            />
            <button
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || loading}
              className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0
                         transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
              style={{ background: 'linear-gradient(135deg, #0ea5e9, #0369a1)' }}>
              <Send className="w-3.5 h-3.5 text-white" />
            </button>
          </div>
          <p className="text-center text-xs text-slate-600 mt-2">
            Press Enter to send · Shift+Enter for new line
          </p>
        </div>
      </div>

      {/* Tool call drawer */}
      {drawerOpen && (
        <ToolCallDrawer toolCalls={toolCalls} onClose={() => setDrawerOpen(false)} />
      )}

      {/* Webhook settings modal */}
      {webhookOpen && <WebhookSettings onClose={() => setWebhookOpen(false)} />}
    </div>
  )
}
