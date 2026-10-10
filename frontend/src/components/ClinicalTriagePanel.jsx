import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Stethoscope, AlertCircle, HelpCircle, CheckCircle2, ChevronRight,
  Sparkles, RefreshCw, AlertTriangle, ShieldAlert, HeartPulse, Check
} from 'lucide-react'

export default function ClinicalTriagePanel({
  clinicalAnalysis,
  diagnosticQuestions = [],
  onAnswerSubmit,
  isRefining = false,
}) {
  const [selectedAnswers, setSelectedAnswers] = useState({})
  const [isExpanded, setIsExpanded] = useState(true)

  if (!clinicalAnalysis && (!diagnosticQuestions || diagnosticQuestions.length === 0)) {
    return null
  }

  const questions = clinicalAnalysis?.questions?.length > 0
    ? clinicalAnalysis.questions
    : diagnosticQuestions

  const {
    primary_complaint = 'Clinical Presentation',
    urgency_tier = 'URGENT',
    urgency_color = 'amber',
    differential_diagnosis = [],
    confirmed_diagnosis = null,
    red_flags = [],
    required_capabilities = [],
    required_equipment = [],
    patient_guidance = '',
    clarification_summary = null,
  } = clinicalAnalysis || {}

  const handleSelectOption = (questionId, option) => {
    setSelectedAnswers((prev) => ({
      ...prev,
      [questionId]: option,
    }))
  }

  const handleRefine = () => {
    if (onAnswerSubmit) {
      onAnswerSubmit(selectedAnswers)
    }
  }

  const answeredCount = Object.keys(selectedAnswers).length
  const totalQuestions = questions.length

  const getUrgencyBadge = () => {
    if (urgency_tier === 'CRITICAL_EMERGENCY') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-extrabold bg-red-100 text-red-800 border border-red-300 shadow-2xs animate-pulse">
          <HeartPulse className="w-3.5 h-3.5 text-red-600" />
          CRITICAL EMERGENCY (Immediate Life-Saving Priority)
        </span>
      )
    }
    if (urgency_tier === 'URGENT') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-900 border border-amber-300">
          <AlertCircle className="w-3.5 h-3.5 text-amber-700" />
          URGENT (Evaluation Needed &lt; 2 Hours)
        </span>
      )
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
        SEMI-URGENT / ROUTINE EVALUATION
      </span>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="card overflow-hidden border-2 border-sky-300/80 shadow-md bg-gradient-to-b from-sky-50/50 via-white to-white"
    >
      {/* Header Banner */}
      <div className="p-4 sm:p-5 border-b border-sky-100 bg-sky-50/80">
        <div className="flex items-start justify-between gap-4 flex-wrap sm:flex-nowrap">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[10px] font-extrabold uppercase tracking-wider bg-medmap-600 text-white px-2.5 py-0.5 rounded-full flex items-center gap-1">
                <Sparkles className="w-3 h-3" />
                Clinical NLP Reasoning &amp; Triage Engine
              </span>
              {getUrgencyBadge()}
            </div>
            <h2 className="text-base sm:text-lg font-bold text-slate-900 flex items-center gap-2">
              <Stethoscope className="w-5 h-5 text-medmap-600 flex-shrink-0" />
              <span>{primary_complaint}</span>
            </h2>
            {clarification_summary && (
              <div className="text-xs text-sky-800 bg-sky-100/80 border border-sky-300 px-3 py-1 rounded-xl font-medium inline-block">
                ✓ {clarification_summary}
              </div>
            )}
          </div>

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-xs text-slate-600 hover:text-slate-900 font-semibold flex items-center gap-1 bg-white border border-slate-200 px-3 py-1.5 rounded-xl shadow-2xs hover:bg-slate-50 transition-colors"
          >
            <span>{isExpanded ? 'Hide Questions' : `Review Diagnosis (${totalQuestions} Questions)`}</span>
            <ChevronRight className={`w-3.5 h-3.5 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
          </button>
        </div>

        {/* Confirmed Diagnosis Highlight */}
        {confirmed_diagnosis && (
          <div className="mt-3 p-3 rounded-xl bg-emerald-50 border border-emerald-300 flex items-center gap-2.5 text-xs text-emerald-950 font-semibold shadow-2xs">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <div>
              <span className="text-[10px] uppercase tracking-wider text-emerald-800 font-bold block">
                Refined Diagnostic Hypothesis
              </span>
              <span>{confirmed_diagnosis}</span>
            </div>
          </div>
        )}
      </div>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="p-4 sm:p-5 space-y-5"
          >
            {/* Top Diagnostics & Red Flags Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 text-xs">
              {/* Differential Diagnosis */}
              {differential_diagnosis.length > 0 && (
                <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/90 space-y-1.5">
                  <div className="font-bold text-slate-700 uppercase tracking-wider text-[10px] flex items-center gap-1.5">
                    <AlertCircle className="w-3.5 h-3.5 text-medmap-600" />
                    <span>Differential Diagnoses Considered</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {differential_diagnosis.map((d, i) => (
                      <span
                        key={i}
                        className={`px-2.5 py-1 rounded-lg font-medium ${
                          i === 0
                            ? 'bg-medmap-100/90 text-medmap-900 border border-medmap-300 font-semibold'
                            : 'bg-white text-slate-700 border border-slate-200'
                        }`}
                      >
                        {i === 0 && <span className="text-medmap-700 font-bold mr-1">#1</span>}
                        {d}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Red Flags / Life-Saving Advisory */}
              {red_flags.length > 0 && (
                <div className="p-3.5 rounded-2xl bg-amber-50/70 border border-amber-200 space-y-1.5">
                  <div className="font-bold text-amber-900 uppercase tracking-wider text-[10px] flex items-center gap-1.5">
                    <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
                    <span>Red Flag Warning Signs</span>
                  </div>
                  <ul className="space-y-1 text-slate-700 text-[11px] pt-1">
                    {red_flags.map((flag, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-amber-600 font-bold">•</span>
                        <span>{flag}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Patient Guidance Alert */}
            {patient_guidance && (
              <div className="p-3 rounded-xl bg-sky-50/80 border border-sky-200 text-xs text-sky-950 flex items-start gap-2 font-medium">
                <HeartPulse className="w-4 h-4 text-sky-600 flex-shrink-0 mt-0.5" />
                <p className="leading-relaxed">
                  <strong className="text-sky-900 font-bold">Actionable Patient Advisory: </strong>
                  {patient_guidance}
                </p>
              </div>
            )}

            {/* Interactive 3 to 5 Genuine Diagnostic Questions */}
            {questions.length > 0 && (
              <div className="pt-2 border-t border-slate-100 space-y-4">
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <div>
                    <h3 className="font-bold text-slate-900 text-sm flex items-center gap-1.5">
                      <HelpCircle className="w-4 h-4 text-medmap-600" />
                      <span>Answer 3 to 5 Diagnostic Questions to Refine Problem Statement</span>
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Select answers below to confirm localized symptoms and pinpoint the best-fit facility.
                    </p>
                  </div>
                  <div className="text-xs font-mono font-semibold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-lg">
                    {answeredCount} of {totalQuestions} answered
                  </div>
                </div>

                <div className="space-y-3.5">
                  {questions.map((q, idx) => {
                    const selected = selectedAnswers[q.id]
                    return (
                      <div
                        key={q.id || idx}
                        className="p-3.5 rounded-2xl bg-white border border-slate-200 shadow-2xs hover:border-sky-300 transition-colors"
                      >
                        <div className="flex items-start justify-between gap-3 mb-2 flex-wrap sm:flex-nowrap">
                          <div className="flex items-start gap-2">
                            <span className="w-5 h-5 rounded-full bg-medmap-50 text-medmap-700 font-bold font-mono text-[11px] flex items-center justify-center flex-shrink-0 mt-0.5 border border-medmap-200">
                              {idx + 1}
                            </span>
                            <span className="text-xs sm:text-sm font-semibold text-slate-900 leading-snug">
                              {q.question}
                            </span>
                          </div>
                          {q.rationale && (
                            <span className="text-[10px] text-slate-500 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded-md font-sans flex-shrink-0" title={q.rationale}>
                              Clinical Rationale Available
                            </span>
                          )}
                        </div>

                        {/* Option Chips */}
                        <div className="flex flex-wrap gap-2 pt-1 pl-7">
                          {q.options?.map((opt, optIdx) => {
                            const isChosen = selected === opt
                            return (
                              <button
                                key={optIdx}
                                type="button"
                                onClick={() => handleSelectOption(q.id, opt)}
                                className={`text-xs px-3 py-1.5 rounded-xl border transition-all text-left flex items-center gap-1.5 font-medium ${
                                  isChosen
                                    ? 'bg-medmap-600 text-white border-medmap-700 shadow-xs'
                                    : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-medmap-50 hover:border-medmap-300'
                                }`}
                              >
                                {isChosen ? (
                                  <Check className="w-3.5 h-3.5 flex-shrink-0 text-white" />
                                ) : (
                                  <span className="w-1.5 h-1.5 rounded-full bg-slate-300 flex-shrink-0" />
                                )}
                                <span>{opt}</span>
                              </button>
                            )
                          })}
                        </div>

                        {q.rationale && (
                          <div className="text-[10px] text-slate-400 pl-7 pt-2 flex items-center gap-1">
                            <span className="font-semibold text-slate-500">Why we ask:</span>
                            <span>{q.rationale}</span>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>

                {/* Submit Answers / Refine Search Action Bar */}
                <div className="flex items-center justify-between gap-3 pt-3 border-t border-slate-100 flex-wrap">
                  <div className="text-xs text-slate-500">
                    {answeredCount > 0
                      ? `${answeredCount} response${answeredCount > 1 ? 's' : ''} ready to recalculate facility fitness`
                      : 'Choose options to refine hospital recommendations'}
                  </div>

                  <div className="flex items-center gap-2">
                    {answeredCount > 0 && (
                      <button
                        type="button"
                        onClick={() => setSelectedAnswers({})}
                        className="text-xs text-slate-500 hover:text-slate-800 px-3 py-1.5 rounded-xl transition-colors font-medium"
                      >
                        Reset Choices
                      </button>
                    )}

                    <button
                      type="button"
                      onClick={handleRefine}
                      disabled={isRefining || answeredCount === 0}
                      className={`btn-primary text-xs py-2 px-4 shadow-sm flex items-center gap-2 rounded-xl transition-all ${
                        isRefining || answeredCount === 0
                          ? 'opacity-60 cursor-not-allowed bg-slate-400'
                          : 'bg-medmap-600 hover:bg-medmap-700 active:scale-98'
                      }`}
                    >
                      {isRefining ? (
                        <>
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          <span>Recalculating Facility Fitness...</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-3.5 h-3.5" />
                          <span>Refine Diagnosis &amp; Re-rank Facilities ({answeredCount})</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
