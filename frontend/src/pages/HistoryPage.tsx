import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowLeft, Clock, Wrench, ChevronDown, ChevronRight,
  Coins, Bot, Loader2
} from 'lucide-react'
import { getHistory, type RunRecord, type ToolCallRecord } from '@/lib/api'
import { formatDate, totalCost } from '@/lib/utils'

const TOOL_COLORS: Record<string, string> = {
  rag_search:            'bg-violet-950/60 text-violet-400 border-violet-800/40',
  classify_destination:  'bg-amber-950/60  text-amber-400  border-amber-800/40',
  get_weather:           'bg-cyan-950/60   text-cyan-400   border-cyan-800/40',
}
const TOOL_LABELS: Record<string, string> = {
  rag_search: 'RAG', classify_destination: 'ML', get_weather: 'Weather',
}

function ToolBadge({ name }: { name: string }) {
  const color = TOOL_COLORS[name] ?? 'bg-slate-800 text-slate-400 border-slate-700'
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium border ${color}`}>
      {TOOL_LABELS[name] ?? name}
    </span>
  )
}

function ToolRow({ tc }: { tc: ToolCallRecord }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="rounded-lg border border-slate-800 overflow-hidden text-xs">
      <button className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-slate-800/40 transition-colors"
              onClick={() => setOpen(v => !v)}>
        <ToolBadge name={tc.tool_name} />
        <span className="text-slate-400 font-mono truncate flex-1 text-[11px]">
          {Object.entries(tc.input_args).map(([k, v]) => `${k}=${JSON.stringify(v)}`).join(', ')}
        </span>
        {open ? <ChevronDown className="w-3 h-3 text-slate-500 shrink-0" />
               : <ChevronRight className="w-3 h-3 text-slate-500 shrink-0" />}
      </button>
      {open && tc.output && (
        <pre className="px-3 pb-3 text-[11px] text-slate-300 whitespace-pre-wrap font-mono
                        border-t border-slate-800 max-h-40 overflow-y-auto">
          {tc.output}
        </pre>
      )}
    </div>
  )
}

function RunCard({ run }: { run: RunRecord }) {
  const [expanded, setExpanded] = useState(false)
  const uniqueTools = [...new Set(run.tool_calls.map(tc => tc.tool_name))]
  const usage = {
    cheap_in: run.tokens_cheap_in, cheap_out: run.tokens_cheap_out,
    strong_in: run.tokens_strong_in, strong_out: run.tokens_strong_out,
  }
  const totalTokens = run.tokens_cheap_in + run.tokens_cheap_out + run.tokens_strong_in + run.tokens_strong_out

  return (
    <div className="rounded-2xl border border-slate-800 overflow-hidden"
         style={{ background: '#161b25' }}>
      <button className="w-full flex items-start gap-4 p-5 text-left hover:bg-slate-700/10 transition-colors"
              onClick={() => setExpanded(v => !v)}>
        <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 mt-0.5"
             style={{ background: 'linear-gradient(135deg, #0ea5e9, #0369a1)' }}>
          <Bot className="w-4 h-4 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white mb-1 truncate">{run.question}</p>
          <div className="flex items-center gap-3 flex-wrap">
            <span className="flex items-center gap-1 text-xs text-slate-500">
              <Clock className="w-3 h-3" />
              {formatDate(run.created_at)}
            </span>
            <span className="flex items-center gap-1 text-xs text-slate-500">
              <Coins className="w-3 h-3" />
              {totalTokens.toLocaleString()} tokens · ~${totalCost(usage)}
            </span>
            <span className="flex items-center gap-1 text-xs text-slate-500">
              <Wrench className="w-3 h-3" />
              {run.tool_calls.length} calls
            </span>
            <div className="flex gap-1 flex-wrap">
              {uniqueTools.map(t => <ToolBadge key={t} name={t} />)}
            </div>
          </div>
        </div>
        <div className="shrink-0 mt-1">
          {expanded
            ? <ChevronDown className="w-4 h-4 text-slate-500" />
            : <ChevronRight className="w-4 h-4 text-slate-500" />}
        </div>
      </button>

      {expanded && (
        <div className="px-5 pb-5 space-y-4 border-t border-slate-800">
          {run.answer && (
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 mt-4">Answer</p>
              <div className="text-sm text-slate-200 leading-relaxed prose-chat"
                   dangerouslySetInnerHTML={{ __html: run.answer.slice(0, 600) + (run.answer.length > 600 ? '…' : '') }} />
            </div>
          )}
          {run.tool_calls.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Tool Calls</p>
              <div className="space-y-1.5">
                {run.tool_calls.map((tc, i) => <ToolRow key={i} tc={tc} />)}
              </div>
            </div>
          )}
          <div className="grid grid-cols-2 gap-2 pt-1">
            {[
              ['Cheap in', run.tokens_cheap_in], ['Cheap out', run.tokens_cheap_out],
              ['Strong in', run.tokens_strong_in], ['Strong out', run.tokens_strong_out],
            ].map(([label, val]) => (
              <div key={label as string} className="px-3 py-2 rounded-lg text-xs"
                   style={{ background: '#1e2535' }}>
                <span className="text-slate-500">{label}: </span>
                <span className="text-slate-200 font-mono">{(val as number).toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default function HistoryPage() {
  const [runs, setRuns] = useState<RunRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    getHistory()
      .then(setRuns)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="min-h-screen" style={{ background: '#0f1117' }}>
      <div className="max-w-3xl mx-auto px-4 py-8">
        <div className="flex items-center gap-3 mb-8">
          <button onClick={() => navigate('/chat')}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-700/50 transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-white">Trip History</h1>
            <p className="text-sm text-slate-400">Your past travel planning sessions</p>
          </div>
        </div>

        {loading && (
          <div className="flex justify-center py-16">
            <Loader2 className="w-6 h-6 text-brand-500 animate-spin" />
          </div>
        )}

        {error && (
          <div className="px-4 py-3 rounded-xl text-sm text-red-400 bg-red-950/40 border border-red-800/50">
            {error}
          </div>
        )}

        {!loading && runs.length === 0 && !error && (
          <div className="text-center py-16 text-slate-500">
            <p>No trips planned yet.</p>
            <button onClick={() => navigate('/chat')}
              className="mt-3 text-sm text-brand-400 hover:text-brand-300 transition-colors">
              Start planning →
            </button>
          </div>
        )}

        <div className="space-y-3">
          {runs.map(run => <RunCard key={run.id} run={run} />)}
        </div>
      </div>
    </div>
  )
}
