import { useRef } from 'react'
import { Search, Loader2, X } from 'lucide-react'
import { motion } from 'framer-motion'

export default function SearchBar({ query, setQuery, onSearch, isSearching }) {
  const inputRef = useRef(null)

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !isSearching) onSearch()
  }

  return (
    <motion.div
      className="relative"
      initial={{ scale: 0.98, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <div className="relative flex items-center bg-white border border-gray-300 rounded-2xl shadow-sm hover:border-gray-400 focus-within:border-medmap-500 focus-within:ring-2 focus-within:ring-medmap-500/20 overflow-hidden transition-all duration-200">
        <Search className="absolute left-5 w-5 h-5 text-slate-400 flex-shrink-0" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe what you need - specialty, location, condition..."
          className="flex-1 bg-transparent text-slate-900 placeholder-slate-400 pl-14 pr-4 py-5 text-base focus:outline-none"
          disabled={isSearching}
        />
        {query && !isSearching && (
          <button
            onClick={() => setQuery('')}
            className="px-3 text-slate-400 hover:text-slate-600 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        )}
        <button
          onClick={() => onSearch()}
          disabled={isSearching || !query.trim()}
          className="flex items-center gap-2 bg-medmap-600 hover:bg-medmap-700 disabled:bg-gray-200 disabled:text-gray-400 text-white font-semibold px-7 py-5 transition-all duration-200 text-sm"
        >
          {isSearching ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="hidden sm:block">Searching...</span>
            </>
          ) : (
            <>
              <Search className="w-4 h-4" />
              <span className="hidden sm:block">Search</span>
            </>
          )}
        </button>
      </div>
    </motion.div>
  )
}
