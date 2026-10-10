import { Shield, ShieldAlert, ShieldCheck } from 'lucide-react'

const getTrustTier = (score) => {
  if (score >= 75) return { label: 'High Trust', color: 'trust-badge-high', icon: ShieldCheck }
  if (score >= 40) return { label: 'Medium Trust', color: 'trust-badge-medium', icon: Shield }
  return { label: 'Low Trust', color: 'trust-badge-low', icon: ShieldAlert }
}

export default function TrustScoreBadge({ score, size = 'md', showScore = true }) {
  const tier = getTrustTier(score)
  const Icon = tier.icon

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-sm px-3 py-1.5 gap-1.5',
    lg: 'text-base px-4 py-2 gap-2',
  }

  const iconSize = { sm: 'w-3 h-3', md: 'w-4 h-4', lg: 'w-5 h-5' }

  return (
    <div className="flex items-center gap-3">
      <span className={`inline-flex items-center font-semibold rounded-full border ${tier.color} ${sizeClasses[size]}`}>
        <Icon className={iconSize[size]} />
        {tier.label}
      </span>
      {showScore && (
        <span className="font-mono text-slate-900 font-bold text-lg">
          {score}<span className="text-slate-400 text-sm font-normal">/100</span>
        </span>
      )}
    </div>
  )
}
