import { useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle, Search, Database, Globe, BarChart2, Loader2, ShieldCheck, Sparkles, AlertCircle } from 'lucide-react'

const STEP_ICONS = {
  query_parse: Search,
  vector_search: Database,
  filter: BarChart2,
  trust_score: AlertCircle,
  validator: ShieldCheck,
  tavily: Globe,
  rank: CheckCircle,
  complete: Sparkles,
  error: AlertCircle,
}

const STEP_STYLES = {
  query_parse:   'text-slate-700 bg-slate-50 border-slate-200',
  vector_search: 'text-blue-800 bg-blue-50/70 border-blue-200',
  filter:        'text-indigo-800 bg-indigo-50/70 border-indigo-200',
  trust_score:   'text-amber-800 bg-amber-50/70 border-amber-200',
  validator:     'text-purple-800 bg-purple-50/70 border-purple-200',
  tavily:        'text-emerald-800 bg-emerald-50/70 border-emerald-200',
  rank:          'text-slate-700 bg-slate-50 border-slate-200',
  complete:      'text-emerald-800 bg-emerald-50 border-emerald-300 font-medium',
  error:         'text-red-700 bg-red-50 border-red-200',
}

export default function AgentThinkingPanel({ steps, isStreaming }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [steps])

  if (steps.length === 0 && !isStreaming) {
    return (
      <div className="card p-5 h-fit">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="w-4 h-4 text-medmap-600" />
          <h3 className="font-semibold text-slate-800 text-sm">Agentic Reasoning Trace</h3>
        </div>
        <div className="text-center py-8 text-slate-400">
          <Database className="w-8 h-8 mx-auto mb-2 opacity-30 text-medmap-600" />
          <p className="text-xs text-slate-500 max-w-xs mx-auto">
            Run a search to observe the multi-agent reasoning chain (Triage Agent → Retrieval → Capability Verification → Contradiction Scorer → IPHS Validator Agent).
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="card overflow-hidden h-fit max-h-[75vh] flex flex-col shadow-sm">
      <div className="flex items-center gap-2 p-3.5 border-b border-gray-100 flex-shrink-0 bg-slate-50/80">
        <div className={`w-2 h-2 rounded-full ${isStreaming ? 'bg-medmap-500 animate-pulse' : 'bg-emerald-500'}`} />
        <Sparkles className="w-4 h-4 text-medmap-600" />
        <h3 className="font-bold text-slate-800 text-xs uppercase tracking-wider">Multi-Agent Reasoning Trace</h3>
        {isStreaming && (
          <Loader2 className="w-3.5 h-3.5 text-medmap-600 animate-spin ml-auto" />
        )}
      </div>

      <div className="overflow-y-auto flex-1 p-3.5 space-y-2.5">
        <AnimatePresence>
          {steps.map((step, i) => {
            const Icon = STEP_ICONS[step.type] || Sparkles
            const styleClass = STEP_STYLES[step.type] || STEP_STYLES.rank

            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.2 }}
                className={`flex items-start gap-2.5 text-xs rounded-lg p-2.5 border ${styleClass}`}
              >
                <div className="flex items-center gap-1.5 flex-shrink-0 mt-0.5">
                  <span className="font-mono text-[10px] text-slate-400">0{i + 1}</span>
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-1 mb-0.5">
                    <span className="font-bold text-slate-800 text-xs">
                      {step.title || step.type?.replace(/_/g, ' ')}
                    </span>
                    {step.agent && (
                      <span className="text-[9px] font-mono uppercase bg-white/70 px-1.5 py-0.2 rounded border border-black/5 text-slate-600">
                        {step.agent}
                      </span>
                    )}
                  </div>
                  {step.message && (
                    <div className="text-slate-600 leading-relaxed text-[11px] font-sans">
                      {step.message}
                    </div>
                  )}
                  {step.count !== undefined && (
                    <div className="font-mono text-[10px] text-slate-500 mt-1">
                      Target corpus: {step.count.toLocaleString()} records
                    </div>
                  )}
                </div>
              </motion.div>
            )
          })}
        </AnimatePresence>

        {isStreaming && (
          <div className="flex items-center gap-2 text-xs text-medmap-600 font-medium px-3 py-1.5 bg-medmap-50/60 rounded-md border border-medmap-100">
            <Loader2 className="w-3 h-3 animate-spin" />
            <span>Agent verifying facilities & cross-checking medical standards...</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  )
}
