import { useRef, useState } from 'react'
import { Search, Loader2, X, MapPin, Navigation, Crosshair, ChevronDown, Check } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

const POPULAR_LOCATIONS = [
  { name: 'Patna Urban', region: 'Bihar' },
  { name: 'Saharsa', region: 'Bihar (Rural Crisis)' },
  { name: 'Lalganj, Vaishali', region: 'Bihar' },
  { name: 'Sheohar', region: 'Bihar' },
  { name: 'Lucknow', region: 'Uttar Pradesh' },
  { name: 'Vrindavan', region: 'Uttar Pradesh' },
  { name: 'New Delhi', region: 'Delhi NCR' },
]

export default function SearchBar({
  query,
  setQuery,
  onSearch,
  isSearching,
  locationText,
  setLocationText,
  onAutoDetectLocation,
  isDetectingLocation,
  locationSource,
}) {
  const inputRef = useRef(null)
  const [showLocationDropdown, setShowLocationDropdown] = useState(false)
  const [tempLocation, setTempLocation] = useState('')

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !isSearching) onSearch()
  }

  const applyLocation = (loc) => {
    setLocationText(loc)
    setShowLocationDropdown(false)
  }

  return (
    <motion.div
      className="relative space-y-2.5"
      initial={{ scale: 0.98, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* Main Search Input Bar */}
      <div className="relative flex flex-col md:flex-row items-stretch bg-white border border-gray-300 rounded-2xl shadow-sm hover:border-gray-400 focus-within:border-medmap-500 focus-within:ring-2 focus-within:ring-medmap-500/20 overflow-hidden transition-all duration-200">
        
        {/* Clinical Problem Input */}
        <div className="relative flex items-center flex-1 min-w-0">
          <Search className="absolute left-5 w-5 h-5 text-slate-400 flex-shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe clinical problem (e.g. emergency appendectomy, ICU ventilator, dialysis)..."
            className="flex-1 bg-transparent text-slate-900 placeholder-slate-400 pl-14 pr-4 py-4 md:py-5 text-base focus:outline-none"
            disabled={isSearching}
          />
          {query && !isSearching && (
            <button
              onClick={() => setQuery('')}
              className="px-3 text-slate-400 hover:text-slate-600 transition-colors"
              title="Clear search"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Location Selector Divider & Button */}
        <div className="border-t md:border-t-0 md:border-l border-gray-200 flex items-center bg-slate-50/70 md:bg-transparent px-3 py-2 md:py-0">
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowLocationDropdown(!showLocationDropdown)}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-100 transition-colors border border-slate-200 md:border-transparent"
            >
              <MapPin className="w-3.5 h-3.5 text-medmap-600 flex-shrink-0" />
              <span className="max-w-[140px] truncate">
                {locationText || 'Auto-detect Location'}
              </span>
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </button>

            {/* Location Selector Dropdown */}
            <AnimatePresence>
              {showLocationDropdown && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 4 }}
                  className="absolute right-0 top-full mt-2 w-72 bg-white rounded-2xl shadow-xl border border-slate-200 p-3 z-50 text-left"
                >
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                    Patient Proximity Reference
                  </div>

                  {/* 1-Click Auto-Detect Button */}
                  <button
                    type="button"
                    onClick={() => {
                      onAutoDetectLocation()
                      setShowLocationDropdown(false)
                    }}
                    disabled={isDetectingLocation}
                    className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl bg-sky-50 hover:bg-sky-100 text-sky-800 text-xs font-semibold transition-colors mb-2 border border-sky-200"
                  >
                    {isDetectingLocation ? (
                      <Loader2 className="w-4 h-4 animate-spin text-sky-600" />
                    ) : (
                      <Crosshair className="w-4 h-4 text-sky-600" />
                    )}
                    <span>Use My Real-Time Location (GPS / IP)</span>
                  </button>

                  {/* Custom Location Input */}
                  <div className="mb-3">
                    <label className="text-[10px] text-slate-500 font-medium block mb-1">
                      Or type city / district / PIN code:
                    </label>
                    <div className="flex gap-1.5">
                      <input
                        type="text"
                        value={tempLocation}
                        onChange={(e) => setTempLocation(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && tempLocation.trim()) {
                            applyLocation(tempLocation.trim())
                          }
                        }}
                        placeholder="e.g. Saharsa, 852200"
                        className="flex-1 text-xs px-2.5 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:border-medmap-500 font-sans"
                      />
                      <button
                        type="button"
                        onClick={() => {
                          if (tempLocation.trim()) applyLocation(tempLocation.trim())
                        }}
                        className="px-2.5 py-1.5 bg-medmap-600 hover:bg-medmap-700 text-white rounded-lg text-xs font-semibold"
                      >
                        Set
                      </button>
                    </div>
                  </div>

                  {/* Preset Locations */}
                  <div className="text-[10px] text-slate-400 font-semibold mb-1">
                    Quick Indian Medical Hubs:
                  </div>
                  <div className="space-y-0.5 max-h-40 overflow-y-auto">
                    {POPULAR_LOCATIONS.map((loc) => (
                      <button
                        key={loc.name}
                        type="button"
                        onClick={() => applyLocation(loc.name)}
                        className="w-full text-left px-2.5 py-1.5 rounded-lg text-xs hover:bg-slate-50 flex items-center justify-between text-slate-700"
                      >
                        <span className="font-medium">{loc.name}</span>
                        <span className="text-[10px] text-slate-400">{loc.region}</span>
                      </button>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Quick Auto-Detect Trigger Button */}
          <button
            type="button"
            onClick={onAutoDetectLocation}
            disabled={isDetectingLocation}
            title="Auto-detect real-time GPS coordinates"
            className="p-2 text-slate-500 hover:text-medmap-600 hover:bg-slate-100 rounded-xl transition-colors ml-1"
          >
            {isDetectingLocation ? (
              <Loader2 className="w-4 h-4 animate-spin text-medmap-600" />
            ) : (
              <Crosshair className="w-4 h-4" />
            )}
          </button>
        </div>

        {/* Submit Search Button */}
        <button
          onClick={() => onSearch()}
          disabled={isSearching || !query.trim()}
          className="flex items-center justify-center gap-2 bg-medmap-600 hover:bg-medmap-700 disabled:bg-gray-200 disabled:text-gray-400 text-white font-semibold px-7 py-4 md:py-5 transition-all duration-200 text-sm flex-shrink-0"
        >
          {isSearching ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Analyzing...</span>
            </>
          ) : (
            <>
              <Search className="w-4 h-4" />
              <span>Find Best Fit</span>
            </>
          )}
        </button>
      </div>

      {/* Active Location Indicator Bar */}
      <div className="flex items-center justify-between px-2 text-xs text-slate-500">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="flex items-center gap-1 font-medium text-slate-600">
            <Navigation className="w-3.5 h-3.5 text-sky-600" />
            Proximity Target:
          </span>
          <span className="bg-sky-50 text-sky-800 border border-sky-200 px-2 py-0.5 rounded-md font-semibold">
            {locationText || 'Auto-detect (Real-time GPS / IP)'}
          </span>
          {locationSource && (
            <span className="text-[10px] font-mono text-slate-400 uppercase">
              [{locationSource}]
            </span>
          )}
          {locationText && (
            <button
              onClick={() => setLocationText('')}
              className="text-[10px] text-slate-400 hover:text-slate-600 underline"
            >
              Reset to Auto
            </button>
          )}
        </div>

        <div className="hidden sm:flex items-center gap-1.5 text-[11px] text-slate-400">
          <span>Sorts by:</span>
          <span className="font-semibold text-slate-600">Trust Score &times; Proximity &times; Standards</span>
        </div>
      </div>
    </motion.div>
  )
}
