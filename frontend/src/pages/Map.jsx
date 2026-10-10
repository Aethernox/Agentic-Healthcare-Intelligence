import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Filter, Layers, Search, MapPin, AlertTriangle, ShieldCheck, ShieldAlert,
  Phone, Building2, CheckCircle2, XCircle, Stethoscope, Compass
} from 'lucide-react'
import MapDashboard from '../components/MapDashboard'
import TrustScoreBadge from '../components/TrustScoreBadge'

const TRUST_FILTERS = ['All', 'High Trust', 'Medium Trust', 'Low Trust']
const SPECIALTY_FILTERS = ['All Specialties', 'ICU', 'Surgery', 'Dialysis', 'Oncology', 'NICU', 'Trauma', 'Emergency']

const DESERT_LAYERS = [
  { id: 'all', label: 'All High-Risk Medical Deserts' },
  { id: 'dialysis', label: 'Dialysis Deserts (No Hemodialysis)' },
  { id: 'oncology', label: 'Oncology Deserts (Zero Cancer Care)' },
  { id: 'trauma', label: 'Trauma & Emergency Deserts' },
]

const QUICK_PINS = [
  { pin: '852200', name: 'Saharsa, Bihar' },
  { pin: '844121', name: 'Lalganj, Vaishali' },
  { pin: '843329', name: 'Sheohar (Critical)' },
  { pin: '271801', name: 'Bahraich, UP' },
  { pin: '800001', name: 'Patna Urban' },
]

const TRUST_DOT = {
  'High Trust': 'bg-emerald-500',
  'Medium Trust': 'bg-amber-400',
  'Low Trust': 'bg-red-500',
}

export default function MapPage() {
  const [trustFilter, setTrustFilter] = useState('All')
  const [specialtyFilter, setSpecialtyFilter] = useState('All Specialties')
  const [selectedHospital, setSelectedHospital] = useState(null)
  const [showDeserts, setShowDeserts] = useState(true)
  const [desertType, setDesertType] = useState('all')
  const [pinInput, setPinInput] = useState('')
  const [searchedPin, setSearchedPin] = useState('')

  const handlePinSearch = (e) => {
    e.preventDefault()
    if (pinInput.trim()) {
      setSearchedPin(pinInput.trim())
    }
  }

  return (
    <div className="h-[calc(100vh-4rem)] flex overflow-hidden">
      {/* Left Sidebar */}
      <div className="w-80 flex-shrink-0 bg-white border-r border-gray-200 flex flex-col overflow-hidden z-10 shadow-sm">
        <div className="p-4 border-b border-gray-100 flex items-center justify-between">
          <h2 className="font-bold text-slate-900 flex items-center gap-2 text-sm uppercase tracking-wider">
            <Filter className="w-4 h-4 text-medmap-600" />
            Crisis Map Controls
          </h2>
          <span className="text-[10px] bg-slate-100 font-mono px-2 py-0.5 rounded text-slate-600 font-semibold">
            PS-03
          </span>
        </div>

        <div className="p-4 space-y-6 overflow-y-auto flex-1">
          {/* PIN Code Quick Search */}
          <div>
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-2 flex items-center gap-1.5">
              <Search className="w-3.5 h-3.5 text-slate-400" />
              PIN Code Desert Inspector
            </label>
            <form onSubmit={handlePinSearch} className="flex gap-1.5 mb-2">
              <input
                type="text"
                placeholder="Enter PIN (e.g. 852200)"
                value={pinInput}
                onChange={(e) => setPinInput(e.target.value)}
                className="input-field text-xs py-1.5 px-3 flex-1 font-mono"
              />
              <button type="submit" className="btn-primary text-xs py-1.5 px-3">
                Go
              </button>
            </form>
            <div className="flex flex-wrap gap-1">
              {QUICK_PINS.map((p) => (
                <button
                  key={p.pin}
                  onClick={() => {
                    setPinInput(p.pin)
                    setSearchedPin(p.pin)
                  }}
                  className="text-[10px] font-mono bg-slate-100 hover:bg-medmap-50 hover:text-medmap-700 border border-slate-200 px-2 py-0.5 rounded transition-colors text-slate-600"
                >
                  {p.pin}
                </button>
              ))}
            </div>
          </div>

          {/* Dynamic Medical Desert Layers */}
          <div>
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-2 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-red-500" />
                Regional Crisis Overlays
              </span>
              <input
                type="checkbox"
                checked={showDeserts}
                onChange={(e) => setShowDeserts(e.target.checked)}
                className="rounded text-medmap-600 focus:ring-medmap-500 cursor-pointer"
              />
            </label>
            {showDeserts && (
              <div className="space-y-1 bg-red-50/40 p-2 rounded-lg border border-red-100">
                {DESERT_LAYERS.map((layer) => (
                  <button
                    key={layer.id}
                    onClick={() => setDesertType(layer.id)}
                    className={`w-full text-left px-2.5 py-1.5 rounded-md text-xs transition-all duration-150 flex items-center justify-between ${
                      desertType === layer.id
                        ? 'bg-red-500 text-white font-semibold shadow-xs'
                        : 'text-slate-700 hover:bg-red-100/60'
                    }`}
                  >
                    <span>{layer.label}</span>
                    {desertType === layer.id && <CheckCircle2 className="w-3 h-3 text-white" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Trust Score Filter */}
          <div>
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-2">
              Trust Score Tier
            </label>
            <div className="space-y-1">
              {TRUST_FILTERS.map((f) => (
                <button
                  key={f}
                  onClick={() => setTrustFilter(f)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-all duration-150 flex items-center justify-between ${
                    trustFilter === f
                      ? 'bg-medmap-50 text-medmap-700 border border-medmap-200 font-semibold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {TRUST_DOT[f] && (
                      <span className={`w-2 h-2 rounded-full flex-shrink-0 ${TRUST_DOT[f]}`} />
                    )}
                    <span>{f}</span>
                  </div>
                  {f === 'Low Trust' && (
                    <span className="text-[10px] text-red-600 font-mono font-normal">Contradictions</span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Specialty Filter */}
          <div>
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-2">
              Verified Specialty
            </label>
            <div className="space-y-1">
              {SPECIALTY_FILTERS.map((f) => (
                <button
                  key={f}
                  onClick={() => setSpecialtyFilter(f)}
                  className={`w-full text-left px-3 py-1.5 rounded-lg text-xs transition-all duration-150 ${
                    specialtyFilter === f
                      ? 'bg-medmap-50 text-medmap-700 border border-medmap-200 font-semibold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-gray-50'
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>

          {/* Legend */}
          <div>
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-2">
              Map Legend
            </label>
            <div className="space-y-2 text-xs bg-slate-50 p-3 rounded-lg border border-slate-100">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-emerald-500 border border-white shadow-2xs" />
                <span className="text-slate-700">High Trust (75-100) &bull; Verified Functional</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-amber-400 border border-white shadow-2xs" />
                <span className="text-slate-700">Medium Trust (40-74) &bull; Conditional</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500 border border-white shadow-2xs" />
                <span className="text-slate-700">Low Trust (0-39) &bull; Contradiction / Ghost</span>
              </div>
              {showDeserts && (
                <div className="flex items-center gap-2 pt-1 border-t border-slate-200">
                  <div className="w-3.5 h-3.5 rounded-full border-2 border-red-500 border-dashed bg-red-500/20" />
                  <span className="text-red-700 font-semibold">High-Risk Medical Desert Zone</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Map Area */}
      <div className="flex-1 relative">
        <MapDashboard
          trustFilter={trustFilter}
          specialtyFilter={specialtyFilter}
          showDeserts={showDeserts}
          desertType={desertType}
          searchedPin={searchedPin}
          onSelectHospital={setSelectedHospital}
        />

        {/* Selected Hospital Detailed Inspector Drawer */}
        <AnimatePresence>
          {selectedHospital && (
            <motion.div
              className="absolute top-4 right-4 w-96 card p-5 shadow-xl bg-white/95 backdrop-blur-md border border-slate-200 max-h-[90vh] overflow-y-auto z-30"
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 30 }}
              transition={{ duration: 0.2 }}
            >
              <div className="flex items-start justify-between mb-3 border-b border-slate-100 pb-3">
                <div className="pr-2">
                  <h3 className="font-bold text-slate-900 text-sm leading-tight">
                    {selectedHospital.name}
                  </h3>
                  {selectedHospital.dataset_row_num && (
                    <span className="text-[10px] font-mono text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200 mt-1 inline-block">
                      dataset.csv Row #{selectedHospital.dataset_row_num}
                    </span>
                  )}
                </div>
                <button
                  onClick={() => setSelectedHospital(null)}
                  className="text-slate-400 hover:text-slate-700 text-xl font-bold leading-none p-1"
                >
                  &times;
                </button>
              </div>

              <div className="flex items-center justify-between mb-3">
                <TrustScoreBadge score={selectedHospital.trust_score} size="md" />
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                  selectedHospital.trust_score >= 75
                    ? 'bg-emerald-100 text-emerald-800'
                    : selectedHospital.trust_score >= 40
                    ? 'bg-amber-100 text-amber-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {selectedHospital.trust_tier?.toUpperCase()} TIER
                </span>
              </div>

              <div className="space-y-1.5 text-xs text-slate-600 mb-4 bg-slate-50 p-3 rounded-lg border border-slate-100">
                <div className="flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-medmap-600 flex-shrink-0" />
                  <span>{selectedHospital.city || selectedHospital.district}, {selectedHospital.state}</span>
                </div>
                {selectedHospital.pin_code && (
                  <div className="font-mono text-slate-700 pl-5">
                    PIN Code: <strong>{selectedHospital.pin_code}</strong>
                  </div>
                )}
                {selectedHospital.phone && (
                  <div className="flex items-center gap-1.5 text-medmap-700 font-semibold pl-5">
                    <Phone className="w-3 h-3" />
                    <a href={`tel:${selectedHospital.phone}`} className="hover:underline">
                      {selectedHospital.phone}
                    </a>
                  </div>
                )}
                {selectedHospital.operator_type && (
                  <div className="flex items-center gap-1.5 text-slate-500 pl-5">
                    <Building2 className="w-3 h-3 text-slate-400" />
                    <span>{selectedHospital.operator_type}</span>
                  </div>
                )}
              </div>

              {/* Contradiction Flags */}
              {selectedHospital.trust_flags && selectedHospital.trust_flags.length > 0 && (
                <div className="mb-4">
                  <div className="text-[11px] font-bold text-red-700 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3 text-red-500" /> Contradiction Flags
                  </div>
                  <div className="space-y-1.5">
                    {selectedHospital.trust_flags.map((flag, i) => (
                      <div key={i} className="text-xs text-red-700 bg-red-50 p-2 rounded border border-red-200">
                        {typeof flag === 'string' ? flag : flag.description}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Validator Assessment */}
              {selectedHospital.validator_notes && (
                <div className="mb-4 text-xs bg-emerald-50/70 p-3 rounded-lg border border-emerald-200">
                  <div className="font-bold text-emerald-900 flex items-center gap-1 mb-1">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                    IPHS 2022 Medical Standards Audit
                  </div>
                  <p className="text-slate-700 leading-relaxed">
                    {selectedHospital.validator_notes}
                  </p>
                </div>
              )}

              {/* Capabilities List */}
              {selectedHospital.capabilities && (
                <div>
                  <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                    Claimed Services
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {Array.isArray(selectedHospital.capabilities) ? (
                      selectedHospital.capabilities.map((c) => (
                        <span key={c} className="text-[11px] bg-slate-100 border border-slate-200 px-2 py-0.5 rounded text-slate-700">
                          {c}
                        </span>
                      ))
                    ) : (
                      Object.entries(selectedHospital.capabilities)
                        .filter(([, v]) => v === true)
                        .map(([k]) => (
                          <span key={k} className="text-[11px] bg-slate-100 border border-slate-200 px-2 py-0.5 rounded text-slate-700">
                            {k}
                          </span>
                        ))
                    )}
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
