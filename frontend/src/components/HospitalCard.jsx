import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  MapPin, ChevronDown, Globe, CheckCircle2, XCircle, AlertTriangle,
  Phone, Building2, Stethoscope, FileText, ShieldAlert, ShieldCheck, DollarSign
} from 'lucide-react'
import TrustScoreBadge from './TrustScoreBadge'

const CAPABILITY_LABELS = {
  icu: 'ICU',
  surgery: 'Surgery',
  emergency_24h: '24/7 Emergency',
  dialysis: 'Dialysis',
  nicu: 'NICU',
  oncology: 'Oncology',
  trauma: 'Trauma',
  blood_bank: 'Blood Bank',
}

export default function HospitalCard({ hospital, rank }) {
  const [expanded, setExpanded] = useState(false)

  const {
    dataset_row_num, name, city, district, state, pin_code, address_line,
    phone, website, operator_type, facility_type,
    trust_score, trust_flags = [], detailed_flags = [], citations = [],
    capabilities = {}, functional_capabilities = {}, bed_count, number_doctors,
    accreditation, tavily_verified, tavily_summary, extraction_source, distance_km,
    validator_verdict, validator_notes,
  } = hospital

  const isFailed = validator_verdict === 'FAILED_STANDARDS' || trust_score < 40
  const isConditional = validator_verdict === 'PASSED_WITH_CONDITIONS'

  return (
    <div className={`card overflow-hidden transition-all duration-200 border ${
      isFailed ? 'border-red-200 hover:border-red-300 bg-red-50/20' : 'hover:border-medmap-300 hover:shadow-md'
    }`}>
      <div className="p-5">
        {/* Top Header */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <div className={`w-8 h-8 rounded-lg border flex items-center justify-center text-sm font-mono font-bold flex-shrink-0 mt-0.5 ${
              rank === 1
                ? 'bg-emerald-500 text-white border-emerald-600 shadow-sm'
                : 'bg-gray-100 border-gray-200 text-slate-600'
            }`}>
              {rank}
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="font-bold text-slate-900 text-base leading-tight truncate">
                  {name}
                </h3>
                {dataset_row_num && (
                  <span className="text-[10px] font-mono bg-slate-100 text-slate-600 px-2 py-0.5 rounded border border-slate-200">
                    dataset.csv Row #{dataset_row_num}
                  </span>
                )}
              </div>

              <div className="flex items-center gap-1.5 text-slate-500 text-xs mt-1.5 flex-wrap">
                <MapPin className="w-3.5 h-3.5 text-medmap-600 flex-shrink-0" />
                <span>{city || district}, {state}</span>
                {pin_code && (
                  <>
                    <span className="text-gray-300">|</span>
                    <span className="font-mono text-slate-600">PIN {pin_code}</span>
                  </>
                )}
                {distance_km && (
                  <>
                    <span className="text-gray-300">|</span>
                    <span className="text-medmap-700 font-semibold bg-medmap-50 px-1.5 py-0.5 rounded border border-medmap-200">
                      {distance_km} km
                    </span>
                  </>
                )}
                {operator_type && (
                  <>
                    <span className="text-gray-300">|</span>
                    <span className="text-slate-600 flex items-center gap-1">
                      <Building2 className="w-3 h-3 text-slate-400" />
                      {operator_type}
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
            <TrustScoreBadge score={trust_score} size="md" />
            {validator_verdict && (
              <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full flex items-center gap-1 ${
                isFailed
                  ? 'bg-red-100 text-red-700 border border-red-200'
                  : isConditional
                  ? 'bg-amber-100 text-amber-800 border border-amber-200'
                  : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
              }`}>
                {isFailed ? <ShieldAlert className="w-3 h-3" /> : <ShieldCheck className="w-3 h-3" />}
                {validator_verdict.replace(/_/g, ' ')}
              </span>
            )}
          </div>
        </div>

        {/* Functional Capabilities Tags */}
        <div className="mb-4">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5 flex items-center gap-1">
            <Stethoscope className="w-3 h-3" /> Capabilities Assessment
          </div>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(CAPABILITY_LABELS).map(([capKey, label]) => {
              const funcInfo = functional_capabilities[capKey]
              const hasClaim = capabilities[capKey] === true
              const isFunctional = funcInfo?.status === 'VERIFIED_FUNCTIONAL'
              const isPhantom = funcInfo?.status === 'PHANTOM_CLAIM'

              if (!hasClaim && !isFunctional && !isPhantom) return null

              return (
                <div
                  key={capKey}
                  className={`text-xs px-2.5 py-1 rounded-md flex items-center gap-1.5 border font-medium ${
                    isFunctional
                      ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                      : isPhantom
                      ? 'bg-red-50 text-red-700 border-red-200 line-through opacity-85'
                      : 'bg-amber-50 text-amber-800 border-amber-200'
                  }`}
                  title={funcInfo?.evidence || (hasClaim ? 'Claimed' : 'Not Available')}
                >
                  {isFunctional ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                  ) : isPhantom ? (
                    <XCircle className="w-3.5 h-3.5 text-red-500 flex-shrink-0" />
                  ) : (
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-500 flex-shrink-0" />
                  )}
                  <span>{label}</span>
                  {isPhantom && <span className="text-[9px] uppercase font-bold no-underline text-red-600">(Phantom)</span>}
                </div>
              )
            })}
          </div>
        </div>

        {/* Quick Highlights / Badges */}
        <div className="flex items-center gap-2 flex-wrap mb-2">
          {bed_count !== null && bed_count !== undefined && (
            <span className="text-xs bg-slate-100 border border-slate-200 px-2.5 py-1 rounded-full text-slate-700 font-mono">
              {bed_count} beds
            </span>
          )}
          {number_doctors !== null && number_doctors !== undefined && (
            <span className="text-xs bg-slate-100 border border-slate-200 px-2.5 py-1 rounded-full text-slate-700 font-mono">
              {number_doctors} doctor{number_doctors !== 1 ? 's' : ''}
            </span>
          )}
          {accreditation && (
            <span className="text-xs bg-emerald-50 border border-emerald-200 text-emerald-700 px-2.5 py-1 rounded-full font-medium">
              {accreditation}
            </span>
          )}
          {operator_type?.toLowerCase().includes('government') && (
            <span className="text-xs bg-blue-50 border border-blue-200 text-blue-700 px-2.5 py-1 rounded-full flex items-center gap-1 font-medium">
              <DollarSign className="w-3 h-3" /> Cashless / Subsidized
            </span>
          )}
          {tavily_verified && (
            <span className="text-xs bg-indigo-50 border border-indigo-200 text-indigo-700 px-2.5 py-1 rounded-full flex items-center gap-1">
              <Globe className="w-3 h-3" /> Web Verified
            </span>
          )}
          {trust_flags.length > 0 && (
            <span className="text-xs bg-red-50 border border-red-200 text-red-600 px-2.5 py-1 rounded-full font-medium">
              {trust_flags.length} contradiction flag{trust_flags.length > 1 ? 's' : ''}
            </span>
          )}
        </div>

        {/* Contact info snippet */}
        {(phone || address_line) && (
          <div className="pt-2 text-xs text-slate-500 flex items-center gap-4 flex-wrap border-t border-gray-100 mt-3">
            {phone && (
              <a href={`tel:${phone}`} className="flex items-center gap-1 text-medmap-700 font-semibold hover:underline">
                <Phone className="w-3 h-3" /> {phone}
              </a>
            )}
            {address_line && (
              <span className="text-slate-400 truncate max-w-md">
                {address_line}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Expand toggle */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-5 py-2.5 text-xs text-slate-500 hover:text-slate-700 bg-gray-50/70 hover:bg-gray-100/70 border-t border-gray-100 transition-all duration-150 font-medium"
      >
        <span>Agent Traceability & Medical Standards Audit</span>
        <div className="flex items-center gap-1">
          <span>{expanded ? 'Hide detail' : 'View row citations & audit'}</span>
          <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`} />
        </div>
      </button>

      {/* Expanded detail */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden border-t border-gray-200 bg-slate-50/60"
          >
            <div className="p-5 space-y-4">
              {/* Validator Notes & Standards */}
              {validator_notes && (
                <div className="bg-white border border-gray-200 rounded-lg p-3.5 shadow-sm">
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-medmap-600" />
                    Validator Agent Assessment (IPHS & NMC Check)
                  </h4>
                  <p className="text-xs text-slate-600 leading-relaxed font-sans">
                    {validator_notes}
                  </p>
                </div>
              )}

              {/* Contradiction Flags */}
              {trust_flags.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-red-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-red-500" />
                    Contradiction Penalties ({trust_flags.length})
                  </h4>
                  <div className="space-y-1.5">
                    {trust_flags.map((flag, i) => (
                      <div key={i} className="text-xs text-red-700 bg-red-50 border border-red-200 rounded-lg p-2.5 leading-relaxed">
                        {typeof flag === 'string' ? flag : flag.description}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Row-Level Citations from dataset.csv */}
              {citations && citations.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5 text-slate-500" />
                    Row-Level Citations (India 10k Dataset)
                  </h4>
                  <div className="space-y-2">
                    {citations.map((cite, i) => (
                      <div key={i} className="bg-white border border-slate-200 rounded-lg p-3 text-xs space-y-1 font-mono">
                        <div className="flex items-center justify-between text-slate-400 text-[10px]">
                          <span>Field: <strong className="text-slate-700">{cite.source_field || cite.field || 'record'}</strong></span>
                          {cite.row_num && <span>Row #{cite.row_num}</span>}
                        </div>
                        <div className="text-slate-800 bg-slate-50 p-2 rounded border border-slate-100 text-[11px] font-mono leading-relaxed">
                          "{cite.quote || cite.text}"
                        </div>
                        {cite.contradiction_flag && (
                          <div className="text-[10px] text-red-600 font-semibold font-sans">
                            Flagged for Rule: {cite.contradiction_flag}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tavily Summary */}
              {tavily_summary && (
                <div>
                  <h4 className="text-xs font-bold text-indigo-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                    <Globe className="w-3.5 h-3.5 text-indigo-600" /> External Web Evidence
                  </h4>
                  <p className="text-xs text-slate-600 bg-indigo-50/60 border border-indigo-100 rounded-lg p-3 leading-relaxed">
                    {tavily_summary}
                  </p>
                </div>
              )}

              {/* Raw Extraction Source */}
              {extraction_source && (
                <div className="text-[11px] text-slate-400 font-mono pt-1">
                  Source: {extraction_source}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
