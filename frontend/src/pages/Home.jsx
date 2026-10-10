import { useState, useRef } from 'react'
import { motion, AnimatePresence, useInView } from 'framer-motion'
import {
  MapPin, AlertTriangle, Database, ShieldCheck, Globe, ChevronRight,
  ArrowDown, Sparkles, HeartPulse, Stethoscope, Clock, ShieldAlert,
  Compass, RefreshCw, CheckCircle2
} from 'lucide-react'
import SearchBar from '../components/SearchBar'
import HospitalCard from '../components/HospitalCard'
import AgentThinkingPanel from '../components/AgentThinkingPanel'
import { searchHospitals } from '../utils/api'

const ANANYA_QUERY = 'Nearest facility in rural Bihar that can perform an emergency appendectomy and typically leverages part-time doctors (₹500 cash, Tuesday 2:30 PM)'

const EXAMPLE_QUERIES = [
  { label: "⚡ Ananya's Emergency Appendectomy", query: ANANYA_QUERY },
  { label: "Dialysis Deserts (UP)", query: 'Districts in UP with no dialysis center within 50km' },
  { label: "Functional ICU (Rajasthan)", query: 'ICU-capable hospitals in Rajasthan with functional ventilators and 24/7 resident doctor' },
  { label: "Oncology Deserts (Bihar)", query: 'High-risk oncology deserts in Bihar with zero cancer care within 75km' },
  { label: "Trauma & Blood Bank (Patna)", query: 'Emergency trauma centers near Patna with functional OT and blood bank' },
]

const STATS = [
  { label: 'Facilities Indexed', value: '10,054', sub: 'India 10k Dataset' },
  { label: 'Contradiction Rules', value: '10 IPHS', sub: 'Internal Consistency' },
  { label: 'Row Citations', value: '100%', sub: 'Traceable Evidence' },
  { label: 'Validator Agent', value: 'IPHS 2022', sub: 'Self-Correcting' },
]

const HOW_IT_WORKS = [
  {
    step: '01',
    icon: Database,
    title: 'Decide & Extract',
    body: 'Sifts through messy unstructured equipment logs, doctor specialties, and 24/7 claims in the 10k dataset to verify actual capabilities vs mere listings.',
  },
  {
    step: '02',
    icon: ShieldCheck,
    title: 'Reason & Trust Scoring',
    body: 'Answers complex multi-attribute queries while applying a Trust Scorer (0-100) that flags logical contradictions (e.g. Surgery with no Anesthesiologist).',
  },
  {
    step: '03',
    icon: Globe,
    title: 'Self-Correcting Validator',
    body: 'Cross-references recommendations against Indian Public Health Standards (IPHS 2022 §4.2) and NMC ratios, providing row-level citations for every deduction.',
  },
]

function FadeInSection({ children, delay = 0 }) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: '-60px' })

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 24 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 24 }}
      transition={{ duration: 0.5, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  )
}

export default function Home() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [agentSteps, setAgentSteps] = useState([])
  const [isSearching, setIsSearching] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)
  const [validatorSummary, setValidatorSummary] = useState(null)
  const searchRef = useRef(null)

  const handleSearch = async (q) => {
    const searchQuery = q || query
    if (!searchQuery.trim()) return

    setIsSearching(true)
    setHasSearched(true)
    setResults([])
    setAgentSteps([])
    setValidatorSummary(null)

    setTimeout(() => {
      searchRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 100)

    try {
      const data = await searchHospitals(searchQuery, (step) => {
        setAgentSteps((prev) => [...prev, step])
      })
      setResults(data.results || [])
      setValidatorSummary(data.validator_summary || null)
    } catch (err) {
      console.error('Search failed:', err)
      setAgentSteps((prev) => [...prev, { type: 'error', message: 'Search failed. Please try again.' }])
    } finally {
      setIsSearching(false)
    }
  }

  const runAnanyaScenario = () => {
    setQuery(ANANYA_QUERY)
    handleSearch(ANANYA_QUERY)
  }

  return (
    <div className="min-h-[calc(100vh-4rem)]">

      {/* ── Hero ─────────────────────────────────────────── */}
      {!hasSearched && (
        <section className="relative px-4 pt-16 pb-14 text-center overflow-hidden">
          {/* Subtle gradient backdrop */}
          <div
            className="absolute inset-0 pointer-events-none"
            style={{
              backgroundImage:
                'radial-gradient(circle at 50% 5%, #e0f2fe 0%, transparent 60%), radial-gradient(circle at 85% 65%, #fef3c7 0%, transparent 50%)',
            }}
          />

          <motion.div
            className="relative max-w-4xl mx-auto"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
          >
            <div className="inline-flex items-center gap-2 bg-medmap-50 border border-medmap-200 text-medmap-800 text-xs font-semibold tracking-wide uppercase px-4 py-1.5 rounded-full mb-6">
              <Sparkles className="w-3.5 h-3.5 text-medmap-600" />
              PS-03 Healthcare Intelligence &bull; India 10k Dataset
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 mb-5 leading-[1.12] tracking-tight">
              The Right Care is the Care You Can{' '}
              <span className="text-medmap-600">Actually Find.</span>
            </h1>

            <p className="text-slate-600 text-base sm:text-lg max-w-2xl mx-auto mb-8 leading-relaxed font-sans">
              An agentic healthcare intelligence system with reasoning and verification layers.
              Sifts through 10,000 messy facility records to separate genuine capabilities from phantom claims.
            </p>

            {/* Meet Ananya Persona Highlight Box */}
            <div className="card p-5 mb-8 bg-gradient-to-r from-amber-50/70 via-sky-50/50 to-emerald-50/70 border-amber-200/80 text-left shadow-sm max-w-3xl mx-auto">
              <div className="flex items-start justify-between gap-4 flex-wrap sm:flex-nowrap">
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold uppercase tracking-wider bg-amber-200/80 text-amber-900 px-2 py-0.5 rounded">
                      Meet Ananya's Real Scenario
                    </span>
                    <span className="text-xs text-slate-500 font-medium">Bihar &bull; Tuesday 2:30 PM &bull; ₹500 Cash</span>
                  </div>
                  <p className="text-xs text-slate-700 leading-relaxed">
                    Father experiencing severe abdominal pain. Nearest hospital (15 km) was a phantom ICU with an unplugged oxygen concentrator and no doctor on duty.
                    20 km in the other direction is an equipped clinic buried in a 2022 survey dump. MedMap closes that gap.
                  </p>
                </div>
                <button
                  onClick={runAnanyaScenario}
                  className="btn-primary flex-shrink-0 text-xs py-2 px-4 whitespace-nowrap shadow flex items-center gap-1.5 bg-medmap-600 hover:bg-medmap-700"
                >
                  <HeartPulse className="w-4 h-4 text-white animate-pulse" />
                  Run Ananya's Search
                </button>
              </div>
            </div>
          </motion.div>

          {/* Search Box */}
          <motion.div
            className="relative max-w-4xl mx-auto"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
          >
            <SearchBar
              query={query}
              setQuery={setQuery}
              onSearch={handleSearch}
              isSearching={isSearching}
            />

            {/* Example Queries */}
            <div className="mt-5">
              <p className="text-xs text-slate-400 mb-2.5 font-medium">Test Problem Statement Queries</p>
              <div className="flex flex-wrap justify-center gap-2">
                {EXAMPLE_QUERIES.map((item) => (
                  <button
                    key={item.label}
                    onClick={() => { setQuery(item.query); handleSearch(item.query) }}
                    className="text-xs bg-white hover:bg-medmap-50 border border-slate-200 hover:border-medmap-300 text-slate-700 hover:text-medmap-700 px-3 py-1.5 rounded-lg transition-all duration-150 text-left font-medium shadow-2xs"
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>
          </motion.div>
        </section>
      )}

      {/* ── Stats Bar ──────────────────────────────────────── */}
      {!hasSearched && (
        <section className="border-y border-gray-100 bg-gray-50/70 py-10 px-4">
          <div className="max-w-4xl mx-auto">
            <FadeInSection>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
                {STATS.map((stat) => (
                  <div key={stat.label} className="text-center p-2">
                    <div className="text-3xl font-extrabold text-slate-900 font-mono mb-1">{stat.value}</div>
                    <div className="text-xs font-semibold text-slate-700 uppercase tracking-wider">{stat.label}</div>
                    <div className="text-[11px] text-slate-400 mt-0.5">{stat.sub}</div>
                  </div>
                ))}
              </div>
            </FadeInSection>
          </div>
        </section>
      )}

      {/* ── How it works ───────────────────────────────────── */}
      {!hasSearched && (
        <section className="py-20 px-4">
          <div className="max-w-5xl mx-auto">
            <FadeInSection>
              <div className="text-center mb-14">
                <p className="section-label mb-2">PS-03 System Architecture</p>
                <h2 className="text-3xl sm:text-4xl font-bold text-slate-900">
                  Decide, Reason, and Close the Loop.
                </h2>
                <p className="text-slate-500 mt-3 max-w-xl mx-auto text-sm">
                  Full agentic traceability with row-level citations and IPHS 2022 standards cross-referencing.
                </p>
              </div>
            </FadeInSection>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {HOW_IT_WORKS.map((item, i) => (
                <FadeInSection key={item.step} delay={i * 0.1}>
                  <div className="card p-6 h-full group hover:border-medmap-300 hover:shadow-md transition-all duration-200">
                    <div className="flex items-start justify-between mb-4">
                      <div className="w-10 h-10 rounded-xl bg-medmap-50 border border-medmap-100 flex items-center justify-center group-hover:bg-medmap-100 transition-colors">
                        <item.icon className="w-5 h-5 text-medmap-600" />
                      </div>
                      <span className="font-mono text-xl font-bold text-gray-200">{item.step}</span>
                    </div>
                    <h3 className="font-bold text-slate-900 mb-2 text-base">{item.title}</h3>
                    <p className="text-slate-500 text-xs leading-relaxed">{item.body}</p>
                  </div>
                </FadeInSection>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ── Search anchor + results ─────────────────────────── */}
      <div ref={searchRef}>
        {hasSearched && (
          <div className="px-4 pt-6">
            <div className="max-w-4xl mx-auto">
              <SearchBar
                query={query}
                setQuery={setQuery}
                onSearch={handleSearch}
                isSearching={isSearching}
              />
            </div>
          </div>
        )}

        <AnimatePresence>
          {hasSearched && (
            <motion.div
              className="max-w-7xl mx-auto px-4 py-8 grid grid-cols-1 lg:grid-cols-3 gap-6"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              {/* Agent Thinking Trace */}
              <div className="lg:col-span-1">
                <AgentThinkingPanel steps={agentSteps} isStreaming={isSearching} />
              </div>

              {/* Results & Validator Summary */}
              <div className="lg:col-span-2 space-y-4">
                {/* Validator Summary Card */}
                {validatorSummary && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="card p-4 bg-gradient-to-r from-emerald-50/70 to-sky-50/70 border-emerald-200 shadow-xs"
                  >
                    <div className="flex items-start gap-3">
                      <ShieldCheck className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs font-bold text-emerald-900 uppercase tracking-wider">
                            Medical Standards Audit &bull; Self-Correcting Validator
                          </span>
                          <span className="text-[10px] bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-mono font-semibold">
                            IPHS 2022 Verified
                          </span>
                        </div>
                        <p className="text-xs text-slate-700 leading-relaxed font-sans">
                          {validatorSummary.patient_advisory}
                        </p>
                        {validatorSummary.standards_checked && (
                          <div className="text-[10px] text-slate-500 pt-1 flex items-center gap-2 flex-wrap">
                            <span>Audited against:</span>
                            {validatorSummary.standards_checked.map((s, i) => (
                              <span key={i} className="font-mono bg-white/80 px-1.5 py-0.5 rounded border border-slate-200">
                                {s}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                )}

                {isSearching && results.length === 0 && (
                  <div className="card p-10 text-center">
                    <div className="w-10 h-10 border-3 border-medmap-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-slate-700 font-semibold text-sm">Evaluating 10,000 Facility Reports...</p>
                    <p className="text-slate-400 text-xs mt-1">Cross-referencing equipment logs, staff rosters, and IPHS standards.</p>
                  </div>
                )}

                {results.length > 0 && (
                  <>
                    <div className="flex items-center justify-between py-1">
                      <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                        <span>{results.length} Verified Facilities</span>
                        <span className="text-xs font-normal text-slate-500 font-mono">(Ranked by Trust Score &times; Proximity)</span>
                      </h2>
                    </div>

                    {results.map((hospital, i) => (
                      <motion.div
                        key={hospital.id || i}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.05 }}
                      >
                        <HospitalCard hospital={hospital} rank={i + 1} />
                      </motion.div>
                    ))}
                  </>
                )}

                {!isSearching && hasSearched && results.length === 0 && agentSteps.length > 0 && (
                  <div className="card p-10 text-center">
                    <AlertTriangle className="w-9 h-9 text-amber-500 mx-auto mb-3" />
                    <p className="text-slate-800 font-semibold">No verified facilities matched the criteria</p>
                    <p className="text-slate-500 text-xs mt-1">Try broadening your search or adjusting the location radius.</p>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
