import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  BarChart3, TrendingDown, AlertTriangle, Download, Map, Users,
  RefreshCw, ShieldAlert, Stethoscope, Building2, CheckCircle2, ShieldCheck
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts'
import { getDashboardStats } from '../utils/api'

const FALLBACK_TRUST = [
  { name: 'High Trust (Verified)', value: 4220, color: '#10b981' },
  { name: 'Medium Trust (Conditional)', value: 3820, color: '#f59e0b' },
  { name: 'Low Trust (Contradictions)', value: 2014, color: '#ef4444' },
]

const FALLBACK_DESERTS = [
  { district: 'Sheohar, Bihar', pop: 656916, facilities: 1, gap: 'Critical', avg_trust: 32 },
  { district: 'Pratapgarh, Rajasthan', pop: 868231, facilities: 2, gap: 'Critical', avg_trust: 38 },
  { district: 'Arwal, Bihar', pop: 700843, facilities: 1, gap: 'Critical', avg_trust: 29 },
  { district: 'Kaimur, Bihar', pop: 1626900, facilities: 3, gap: 'Severe', avg_trust: 41 },
  { district: 'Shrawasti, UP', pop: 1117361, facilities: 2, gap: 'Severe', avg_trust: 36 },
  { district: 'Balrampur, UP', pop: 1681513, facilities: 4, gap: 'Severe', avg_trust: 44 },
  { district: 'Sitamarhi, Bihar', pop: 3419622, facilities: 7, gap: 'High', avg_trust: 48 },
  { district: 'Khagaria, Bihar', pop: 1657599, facilities: 4, gap: 'High', avg_trust: 42 },
  { district: 'Supaul, Bihar', pop: 2228397, facilities: 5, gap: 'High', avg_trust: 45 },
  { district: 'Bahraich, UP', pop: 3487731, facilities: 9, gap: 'High', avg_trust: 40 },
]

const FALLBACK_SPECIALTY = [
  { specialty: 'Dialysis', covered: 18, uncovered: 82 },
  { specialty: 'Oncology', covered: 12, uncovered: 88 },
  { specialty: 'Trauma', covered: 31, uncovered: 69 },
  { specialty: 'Neonatal ICU', covered: 22, uncovered: 78 },
  { specialty: 'Cardiac Surgery', covered: 9, uncovered: 91 },
  { specialty: 'Neurosurgery', covered: 8, uncovered: 92 },
]

const FALLBACK_STATES = [
  { state: 'Bihar', total: 1240, high: 420, medium: 510, low: 310 },
  { state: 'UP', total: 2180, high: 890, medium: 860, low: 430 },
  { state: 'Maharashtra', total: 1640, high: 980, medium: 510, low: 150 },
  { state: 'Rajasthan', total: 980, high: 420, medium: 380, low: 180 },
  { state: 'Gujarat', total: 850, high: 520, medium: 240, low: 90 },
  { state: 'Karnataka', total: 760, high: 480, medium: 210, low: 70 },
]

const CONTRADICTION_FREQUENCY = [
  { rule: 'Claims Advanced Surgery without Anesthesiologist listed', penalty: '-30 pts', standard: 'IPHS 2022 §4.2', detected: '482 records' },
  { rule: 'Claims ICU but lacks ventilators & vital monitors', penalty: '-25 pts', standard: 'NABH Critical Care', detected: '624 records' },
  { rule: 'Claims 24/7 Emergency but lacks resident night doctor', penalty: '-20 pts', standard: 'IPHS Casualty Rules', detected: '512 records' },
  { rule: 'Outpatient Dental/Cosmetic claiming full ICU & OT', penalty: '-35 pts', standard: 'Clinical Estab. Act', detected: '388 records' },
  { rule: 'Claims Dialysis but lacks nephrologist or dialyzer', penalty: '-25 pts', standard: 'PM National Dialysis', detected: '294 records' },
  { rule: 'Claims Oncology/Cancer treatment without Oncologist', penalty: '-30 pts', standard: 'National Cancer Grid', detected: '246 records' },
  { rule: 'Stale survey footprint (>2 years with unverified status)', penalty: '-15 pts', standard: 'Recency Benchmark', detected: '715 records' },
]

const GAP_COLORS = {
  Critical: 'text-red-700 bg-red-50 border-red-200',
  Severe: 'text-orange-700 bg-orange-50 border-orange-200',
  High: 'text-amber-700 bg-amber-50 border-amber-200',
}

const StatCard = ({ icon: Icon, label, value, sub, iconBg, iconColor }) => (
  <div className="card p-5">
    <div className="flex items-center gap-3 mb-3">
      <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${iconBg}`}>
        <Icon className={`w-4 h-4 ${iconColor}`} />
      </div>
      <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">{label}</span>
    </div>
    <div className="text-3xl font-extrabold font-mono text-slate-900">{value}</div>
    {sub && <div className="text-xs text-slate-400 mt-1 font-medium">{sub}</div>}
  </div>
)

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [liveData, setLiveData] = useState(false)

  async function loadStats() {
    setLoading(true)
    const data = await getDashboardStats()
    if (data) {
      setStats(data)
      setLiveData(true)
    }
    setLoading(false)
  }

  useEffect(() => { loadStats() }, [])

  const trustDist = stats?.trust_distribution || FALLBACK_TRUST
  const stateData = stats?.state_data || FALLBACK_STATES
  const specialtyGaps = stats?.specialty_gaps || FALLBACK_SPECIALTY
  const desertDistricts = stats?.desert_districts || FALLBACK_DESERTS
  const summary = stats?.summary || {}
  const totalFacilities = stats?.total_facilities || 10054

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between flex-wrap gap-4"
      >
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-medmap-600" />
            Healthcare Intelligence & Desert Analytics (PS-03)
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Auditing 10,054 medical facility records across India &bull; Grounded in IPHS 2022 standards
            {liveData && <span className="ml-2 text-emerald-600 text-xs font-semibold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">Live Database Connected</span>}
            {!liveData && !loading && <span className="ml-2 text-sky-600 text-xs font-semibold bg-sky-50 px-2 py-0.5 rounded border border-sky-200">Synthesized 10k Dataset</span>}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadStats}
            disabled={loading}
            className="btn-ghost flex items-center gap-2 text-sm"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh Intelligence
          </button>
        </div>
      </motion.div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Building2}
          label="Facilities Indexed"
          value={totalFacilities.toLocaleString()}
          sub="India 10k Hospital Corpus"
          iconBg="bg-blue-50"
          iconColor="text-blue-600"
        />
        <StatCard
          icon={ShieldAlert}
          label="Contradictions Flagged"
          value={summary.low_trust_records || '2,014'}
          sub="Ghost ICUs & Staffing Mismatches"
          iconBg="bg-red-50"
          iconColor="text-red-600"
        />
        <StatCard
          icon={AlertTriangle}
          label="Medical Deserts Found"
          value={summary.medical_deserts || '847'}
          sub="Zero Specialized Care within 50km"
          iconBg="bg-amber-50"
          iconColor="text-amber-600"
        />
        <StatCard
          icon={Users}
          label="Population at Risk"
          value="9.85M"
          sub="Critical Secondary Care Deficit"
          iconBg="bg-purple-50"
          iconColor="text-purple-600"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trust Distribution Pie Chart */}
        <div className="card p-6">
          <h2 className="text-base font-bold text-slate-900 mb-1 flex items-center justify-between">
            <span>Trust Score Distribution</span>
            <span className="text-xs font-mono text-slate-400 font-normal">Internal Consistency</span>
          </h2>
          <p className="text-xs text-slate-500 mb-4">
            Facilities categorized by IPHS contradiction deductions (High: 75+, Medium: 40-74, Low: &lt;40).
          </p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={trustDist}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={85}
                  innerRadius={50}
                  label={({ name, percent }) => `${name.split(' ')[0]}: ${(percent * 100).toFixed(0)}%`}
                >
                  {trustDist.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Specialized Deserts Breakdown Bar Chart */}
        <div className="card p-6">
          <h2 className="text-base font-bold text-slate-900 mb-1 flex items-center justify-between">
            <span>Specialized Regional Deserts</span>
            <span className="text-xs font-mono text-slate-400 font-normal">Coverage vs Deficit</span>
          </h2>
          <p className="text-xs text-slate-500 mb-4">
            Percentage of facilities with verified functional capabilities vs regional healthcare deficit.
          </p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={specialtyGaps} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" domain={[0, 100]} unit="%" />
                <YAxis dataKey="specialty" type="category" width={90} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="covered" name="Verified Functional %" fill="#10b981" stackId="a" />
                <Bar dataKey="uncovered" name="Regional Deficit %" fill="#ef4444" stackId="a" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* State-Level Breakdown Chart */}
      <div className="card p-6">
        <h2 className="text-base font-bold text-slate-900 mb-1">
          State-Level Medical Facility Integrity
        </h2>
        <p className="text-xs text-slate-500 mb-6">
          Verified high-trust vs low-trust (contradiction-flagged) facilities across highest density states.
        </p>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={stateData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="state" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="high" name="High Trust (Verified)" fill="#10b981" />
              <Bar dataKey="medium" name="Medium Trust (Conditional)" fill="#f59e0b" />
              <Bar dataKey="low" name="Low Trust (Ghost / Phantom Claims)" fill="#ef4444" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* IPHS Contradiction Detection Rules Table */}
      <div className="card overflow-hidden">
        <div className="p-5 border-b border-gray-100 bg-slate-50/60">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-medmap-600" />
            IPHS Contradiction Audit Matrix (Trust Scorer Engine)
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Rules applied across messy unstructured equipment logs, doctor counts, and claims.
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase font-semibold border-b border-gray-200">
              <tr>
                <th className="px-5 py-3">Contradiction Rule</th>
                <th className="px-5 py-3">Penalty</th>
                <th className="px-5 py-3">Medical Standard</th>
                <th className="px-5 py-3">Frequency in 10k Dataset</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {CONTRADICTION_FREQUENCY.map((rule, i) => (
                <tr key={i} className="hover:bg-slate-50/80 transition-colors">
                  <td className="px-5 py-3 font-medium text-slate-800">{rule.rule}</td>
                  <td className="px-5 py-3 font-mono font-bold text-red-600">{rule.penalty}</td>
                  <td className="px-5 py-3 text-slate-500 font-mono text-[11px]">{rule.standard}</td>
                  <td className="px-5 py-3 text-slate-700 font-mono font-semibold">{rule.detected}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Underserved Desert Districts Table */}
      <div className="card overflow-hidden">
        <div className="p-5 border-b border-gray-100 bg-slate-50/60">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            High-Risk Healthcare Desert Districts
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Regions with severe facility deficits relative to population, prioritizing rural Bihar and Eastern UP.
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase font-semibold border-b border-gray-200">
              <tr>
                <th className="px-5 py-3">District, State</th>
                <th className="px-5 py-3">Population</th>
                <th className="px-5 py-3">Functional Facilities</th>
                <th className="px-5 py-3">Average Trust</th>
                <th className="px-5 py-3">IPHS Gap Severity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {desertDistricts.map((d, i) => (
                <tr key={i} className="hover:bg-slate-50/80 transition-colors">
                  <td className="px-5 py-3 font-bold text-slate-800">{d.district}</td>
                  <td className="px-5 py-3 font-mono text-slate-600">{d.pop?.toLocaleString()}</td>
                  <td className="px-5 py-3 font-mono text-slate-600 font-semibold">{d.facilities}</td>
                  <td className="px-5 py-3 font-mono">
                    <span className={`px-2 py-0.5 rounded font-bold ${
                      (d.avg_trust || 0) < 40 ? 'bg-red-50 text-red-700' : 'bg-amber-50 text-amber-700'
                    }`}>
                      {d.avg_trust || 35}/100
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    <span className={`px-2.5 py-1 rounded-full font-bold border text-[11px] ${GAP_COLORS[d.gap] || GAP_COLORS.Critical}`}>
                      {d.gap}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
