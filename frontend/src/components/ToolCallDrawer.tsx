import { X, Wrench, ChevronDown, ChevronRight } from 'lucide-react'
import { useState } from 'react'
import type { ToolCallRecord } from '@/lib/api'

const TOOL_COLORS: Record<string, string> = {
  rag_search:            'text-violet-400 bg-violet-950/60 border-violet-800/50',
  classify_destination:  'text-amber-400  bg-amber-950/60  border-amber-800/50',
  get_weather:           'text-cyan-400   bg-cyan-950/60   border-cyan-800/50',
}
const TOOL_LABELS: Record<string, string> = {
  rag_search:            'RAG Search',
  classify_destination:  'ML Classifier',
  get_weather:           'Weather API',
}

function ToolCallCard({ tc }: { tc: ToolCallRecord }) {
  const [open, setOpen] = useState(false)
  const color = TOOL_COLORS[tc.tool_name] ?? 'text-slate-400 bg-slate-800/60 border-slate-700/50'
  const label = TOOL_LABELS[tc.tool_name] ?? tc.tool_name

  return (
    <div className={`rounded-xl border text-xs ${color} overflow-hidden`}>
      <button className="w-full flex items-center gap-2 px-3 py-2.5 text-left"
              onClick={() => setOpen(v => !v)}>
        <Wrench className="w-3.5 h-3.5 shrink-0" />
        <span className="font-semibold">{label}</span>
        <span className="font-mono text-[10px] opacity-60 truncate flex-1">
          ({Object.entries(tc.input_args).map(([k, v]) => `${k}=${JSON.stringify(v)}`).join(', ')})
        </span>
        {open ? <ChevronDown className="w-3.5 h-3.5 shrink-0" /> : <ChevronRight className="w-3.5 h-3.5 shrink-0" />}
      </button>

      {open && (
        <div className="px-3 pb-3 space-y-2 border-t border-current/20">
          <div>
            <p className="text-[10px] uppercase tracking-wider opacity-50 mb-1">Input</p>
            <pre className="text-[11px] whitespace-pre-wrap opacity-80 font-mono">
              {JSON.stringify(tc.input_args, null, 2)}
            </pre>
          </div>
          {tc.output && (
            <div>
              <p className="text-[10px] uppercase tracking-wider opacity-50 mb-1">Output</p>
              <pre className="text-[11px] whitespace-pre-wrap opacity-80 font-mono max-h-48 overflow-y-auto">
                {tc.output}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

interface Props {
  toolCalls: ToolCallRecord[]
  onClose: () => void
}

export default function ToolCallDrawer({ toolCalls, onClose }: Props) {
  return (
    <aside className="flex flex-col h-full border-l border-slate-800"
           style={{ background: '#161b25', width: 380 }}>
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <div>
          <h2 className="text-sm font-semibold text-white">Tool Calls</h2>
          <p className="text-xs text-slate-500">{toolCalls.length} invocation{toolCalls.length !== 1 ? 's' : ''}</p>
        </div>
        <button onClick={onClose}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700/50 transition-colors">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {toolCalls.map((tc, i) => (
          <ToolCallCard key={i} tc={tc} />
        ))}
        {toolCalls.length === 0 && (
          <p className="text-slate-500 text-sm text-center pt-8">No tool calls yet</p>
        )}
      </div>
    </aside>
  )
}
