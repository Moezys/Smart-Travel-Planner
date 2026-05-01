import { useState, useEffect, type FormEvent } from 'react'
import { X, Webhook, CheckCircle, Loader2, AlertCircle } from 'lucide-react'
import { getMe, updateWebhook } from '@/lib/api'

interface Props {
  onClose: () => void
}

export default function WebhookSettings({ onClose }: Props) {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getMe()
      .then(me => setUrl(me.webhook_url ?? ''))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  async function handleSave(e: FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError('')
    setSaved(false)
    try {
      await updateWebhook(url.trim() || null)
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
         style={{ background: 'rgba(0,0,0,0.7)' }}
         onClick={onClose}>
      <div className="w-full max-w-md rounded-2xl border border-slate-700/50 p-6 shadow-2xl"
           style={{ background: '#161b25' }}
           onClick={e => e.stopPropagation()}>

        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl flex items-center justify-center"
                 style={{ background: 'linear-gradient(135deg, #7c3aed, #4f46e5)' }}>
              <Webhook className="w-4 h-4 text-white" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Webhook Settings</h2>
              <p className="text-xs text-slate-400">Deliver trip plans to Discord or any URL</p>
            </div>
          </div>
          <button onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700/50 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {loading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="w-5 h-5 text-brand-500 animate-spin" />
          </div>
        ) : (
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Webhook URL
              </label>
              <input
                type="url"
                value={url}
                onChange={e => setUrl(e.target.value)}
                placeholder="https://discord.com/api/webhooks/…"
                className="w-full px-3 py-2.5 rounded-xl text-sm text-white placeholder-slate-500
                           border border-slate-700 outline-none transition-all duration-200
                           focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
                style={{ background: '#0f1117' }}
              />
              <p className="text-xs text-slate-500 mt-1.5">
                Supports Discord webhooks (rich embeds) and any generic HTTP endpoint.
                Leave empty to disable.
              </p>
            </div>

            <div className="rounded-xl p-3 border border-slate-700/50 text-xs text-slate-400 space-y-1"
                 style={{ background: '#1e2535' }}>
              <p className="font-medium text-slate-300">What gets sent</p>
              <p>• Your question and the full trip recommendation</p>
              <p>• Tools used, token count, estimated cost</p>
              <p>• 2 retries with 1s backoff · 10s timeout per attempt</p>
              <p>• Delivery failure never blocks your response</p>
            </div>

            {error && (
              <div className="flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm text-red-400
                              bg-red-950/40 border border-red-800/50">
                <AlertCircle className="w-4 h-4 shrink-0" />
                {error}
              </div>
            )}

            <button type="submit" disabled={saving}
              className="w-full py-2.5 rounded-xl font-medium text-white text-sm
                         transition-all duration-200 disabled:opacity-60 flex items-center justify-center gap-2"
              style={{ background: 'linear-gradient(135deg, #0ea5e9, #0369a1)' }}>
              {saving && <Loader2 className="w-4 h-4 animate-spin" />}
              {saved && <CheckCircle className="w-4 h-4" />}
              {saved ? 'Saved!' : 'Save Webhook'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
