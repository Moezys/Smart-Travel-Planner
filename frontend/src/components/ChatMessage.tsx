import { Bot, User, Coins } from 'lucide-react'
import type { ChatResponse } from '@/lib/api'
import { totalCost } from '@/lib/utils'

export interface Message {
  role: 'user' | 'assistant'
  content: string
  usage?: ChatResponse['token_usage']
}

function renderMarkdown(text: string) {
  // Minimal markdown → HTML (no external dep)
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/^• (.+)$/gm, '<li>$1</li>')
    .replace(/^\* (.+)$/gm, '<li>$1</li>')
    .replace(/^---$/gm, '<hr/>')
    .split('\n')
    .map(line => (line.startsWith('<') ? line : line ? `<p>${line}</p>` : ''))
    .join('\n')
}

export default function ChatMessage({ msg }: { msg: Message }) {
  const isUser = msg.role === 'user'

  if (isUser) {
    return (
      <div className="flex items-end gap-3 justify-end">
        <div className="max-w-[75%] px-4 py-3 rounded-2xl rounded-br-md text-sm text-white"
             style={{ background: 'linear-gradient(135deg, #0ea5e9, #0369a1)' }}>
          {msg.content}
        </div>
        <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0"
             style={{ background: '#1e2535' }}>
          <User className="w-4 h-4 text-slate-400" />
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-start gap-3">
      <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1"
           style={{ background: 'linear-gradient(135deg, #0ea5e9, #0369a1)' }}>
        <Bot className="w-4 h-4 text-white" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm text-slate-100 prose-chat"
             dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }} />
        {msg.usage && (
          <div className="flex items-center gap-1.5 mt-2 text-xs text-slate-500">
            <Coins className="w-3 h-3" />
            <span>{(msg.usage.total_in + msg.usage.total_out).toLocaleString()} tokens</span>
            <span className="opacity-40">·</span>
            <span>~${totalCost(msg.usage)}</span>
          </div>
        )}
      </div>
    </div>
  )
}
