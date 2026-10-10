import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Map, Search, BarChart3, Heart } from 'lucide-react'
import Home from './pages/Home'
import MapPage from './pages/Map'
import Dashboard from './pages/Dashboard'

const navItems = [
  { to: '/', label: 'Search', icon: Search, exact: true },
  { to: '/map', label: 'Map', icon: Map },
  { to: '/dashboard', label: 'Policy View', icon: BarChart3 },
]

function Navbar() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <NavLink to="/" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 rounded-lg bg-medmap-600 flex items-center justify-center shadow-sm">
            <Heart className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-xl text-slate-900 tracking-tight">
            Med<span className="text-medmap-600">Map</span>
          </span>
        </NavLink>

        <div className="flex items-center gap-1">
          {navItems.map(({ to, label, icon: Icon, exact }) => (
            <NavLink
              key={to}
              to={to}
              end={exact}
              className={({ isActive }) =>
                `flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-medmap-50 text-medmap-700 border border-medmap-200'
                    : 'text-slate-500 hover:text-slate-900 hover:bg-gray-100'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              <span className="hidden sm:block">{label}</span>
            </NavLink>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <span className="hidden md:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-pulse" />
            PS-03 Intelligence Engine
          </span>
          <span className="text-xs text-slate-500 font-mono hidden sm:block">10k Dataset</span>
          <div className="w-2 h-2 rounded-full bg-emerald-500" title="System Online" />
        </div>
      </div>
    </nav>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-white">
        <Navbar />
        <motion.main
          className="pt-16"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/map" element={<MapPage />} />
            <Route path="/dashboard" element={<Dashboard />} />
          </Routes>
        </motion.main>
      </div>
    </BrowserRouter>
  )
}
