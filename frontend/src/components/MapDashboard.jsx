import { useEffect, useRef, useState } from 'react'
import { getHospitals, getCrisisMapPins } from '../utils/api'

const getTrustColor = (score) => {
  if (score >= 75) return '#10b981' // emerald
  if (score >= 40) return '#f59e0b' // amber
  return '#ef4444' // red
}

const SPECIALTY_TO_CAP = {
  ICU: 'icu',
  Surgery: 'surgery',
  Emergency: 'emergency_24h',
  Dialysis: 'dialysis',
  Oncology: 'oncology',
  NICU: 'nicu',
  Trauma: 'trauma',
}

export default function MapDashboard({
  trustFilter,
  specialtyFilter,
  showDeserts,
  desertType = 'all',
  searchedPin = '',
  onSelectHospital,
}) {
  const mapRef = useRef(null)
  const mapInstance = useRef(null)
  const markersRef = useRef([])
  const desertLayerRef = useRef([])
  const [mapReady, setMapReady] = useState(false)
  const [hospitals, setHospitals] = useState([])
  const [crisisPins, setCrisisPins] = useState([])
  const [loading, setLoading] = useState(true)

  // Fetch hospital and crisis pin data
  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const filters = {}
        if (trustFilter === 'High Trust') filters.trust_tier = 'high'
        else if (trustFilter === 'Medium Trust') filters.trust_tier = 'medium'
        else if (trustFilter === 'Low Trust') filters.trust_tier = 'low'

        if (specialtyFilter && specialtyFilter !== 'All Specialties') {
          filters.specialty = specialtyFilter
        }

        const [hospData, pinData] = await Promise.all([
          getHospitals({ ...filters, limit: 1000 }),
          getCrisisMapPins(),
        ])

        setHospitals(hospData.hospitals || hospData)
        setCrisisPins(pinData || [])
      } catch (err) {
        console.error('Failed to load map data:', err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [trustFilter, specialtyFilter])

  // Initialise Leaflet map once
  useEffect(() => {
    if (typeof window === 'undefined' || mapInstance.current) return

    import('leaflet').then((L) => {
      const map = L.map(mapRef.current, {
        center: [25.7, 85.5], // Centered around Bihar & Eastern Gangetic Plain
        zoom: 7,
        zoomControl: true,
      })

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap &bull; MedMap PS-03',
        maxZoom: 18,
      }).addTo(map)

      mapInstance.current = map
      setMapReady(true)
    })

    return () => {
      if (mapInstance.current) {
        mapInstance.current.remove()
        mapInstance.current = null
      }
    }
  }, [])

  // Handle searched PIN code zoom
  useEffect(() => {
    if (!mapReady || !mapInstance.current || !searchedPin.trim()) return

    const pinMatch = crisisPins.find(p => p.pin_code === searchedPin.trim())
    if (pinMatch && pinMatch.lat && pinMatch.lng) {
      mapInstance.current.flyTo([pinMatch.lat, pinMatch.lng], 11, { duration: 1.2 })
    } else {
      const hospMatch = hospitals.find(h => h.pin_code === searchedPin.trim())
      if (hospMatch && (hospMatch.lat || hospMatch.latitude)) {
        mapInstance.current.flyTo([hospMatch.lat || hospMatch.latitude, hospMatch.lng || hospMatch.longitude], 12, { duration: 1.2 })
      }
    }
  }, [searchedPin, mapReady, crisisPins, hospitals])

  // Re-render markers and dynamic crisis zones
  useEffect(() => {
    if (!mapReady || !mapInstance.current) return

    import('leaflet').then((L) => {
      // Clear existing markers & layers
      markersRef.current.forEach((m) => m.remove())
      markersRef.current = []

      desertLayerRef.current.forEach((l) => l.remove())
      desertLayerRef.current = []

      // 1. Render Dynamic PIN Code Crisis Deserts
      if (showDeserts) {
        const activePins = crisisPins.filter((pin) => {
          if (desertType === 'dialysis') return pin.dialysis_desert
          if (desertType === 'oncology') return pin.oncology_desert
          if (desertType === 'trauma') return pin.trauma_desert
          return pin.desert_score >= 45
        })

        activePins.forEach((pin) => {
          const isCritical = pin.desert_score >= 70
          const color = isCritical ? '#dc2626' : '#ea580c'

          const circle = L.circle([pin.lat, pin.lng], {
            radius: isCritical ? 24000 : 18000,
            color,
            fillColor: color,
            fillOpacity: isCritical ? 0.16 : 0.10,
            weight: 1.5,
            dashArray: '4, 4',
          }).addTo(mapInstance.current)

          circle.bindTooltip(
            `<div style="font-family: sans-serif; font-size: 11px; padding: 4px;">
              <strong>${pin.severity}</strong><br/>
              PIN Code: <strong>${pin.pin_code}</strong> (${pin.district}, ${pin.state})<br/>
              Crisis Score: <strong>${pin.desert_score}/100</strong><br/>
              Phantom Facilities: <strong>${pin.phantom_facilities} / ${pin.total_facilities}</strong>
            </div>`,
            { direction: 'top', sticky: true }
          )

          desertLayerRef.current.push(circle)
        })
      }

      // 2. Render Medical Facility Markers
      const capKey = SPECIALTY_TO_CAP[specialtyFilter]
      const filtered = hospitals.filter((h) => {
        const lat = h.lat ?? h.latitude
        const lng = h.lng ?? h.longitude
        if (!lat || !lng) return false

        if (trustFilter === 'High Trust' && h.trust_score < 75) return false
        if (trustFilter === 'Medium Trust' && (h.trust_score < 40 || h.trust_score >= 75)) return false
        if (trustFilter === 'Low Trust' && h.trust_score >= 40) return false

        if (capKey) {
          const caps = h.capabilities_map || h.capabilities || {}
          if (typeof caps === 'object' && !Array.isArray(caps)) {
            if (!caps[capKey]) return false
          } else if (Array.isArray(caps)) {
            if (!caps.includes(specialtyFilter)) return false
          }
        }

        return true
      })

      filtered.forEach((hospital) => {
        const lat = hospital.lat ?? hospital.latitude
        const lng = hospital.lng ?? hospital.longitude
        if (!lat || !lng) return

        const color = getTrustColor(hospital.trust_score)
        const isSelected = false

        const icon = L.divIcon({
          className: '',
          html: `<div style="
            width: 14px; height: 14px; border-radius: 50%;
            background: ${color}; border: 2.5px solid #ffffff;
            box-shadow: 0 0 10px ${color}aa, 0 2px 4px rgba(0,0,0,0.4);
            cursor: pointer;
            transition: transform 0.15s ease;
          "></div>`,
          iconSize: [14, 14],
          iconAnchor: [7, 7],
        })

        const marker = L.marker([lat, lng], { icon })
          .addTo(mapInstance.current)
          .on('click', () => {
            onSelectHospital(hospital)
          })

        marker.bindTooltip(
          `<div style="font-family: sans-serif; font-size: 11px;">
            <strong>${hospital.name}</strong><br/>
            Trust Score: <strong style="color: ${color};">${hospital.trust_score}/100</strong> (${hospital.trust_tier || 'tier'})<br/>
            ${hospital.city || hospital.district}, ${hospital.state} | PIN ${hospital.pin_code || 'N/A'}<br/>
            ${hospital.dataset_row_num ? `<span style="color: #64748b;">Row #${hospital.dataset_row_num} in 10k dataset</span>` : ''}
          </div>`,
          { direction: 'top', offset: [0, -8] }
        )

        markersRef.current.push(marker)
      })
    })
  }, [mapReady, hospitals, crisisPins, trustFilter, specialtyFilter, showDeserts, desertType, onSelectHospital])

  return (
    <div className="relative w-full h-full">
      <div ref={mapRef} className="w-full h-full" />
      {(!mapReady || loading) && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-50/80 backdrop-blur-2xs z-20">
          <div className="text-center">
            <div className="w-10 h-10 border-3 border-medmap-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            <p className="text-slate-700 font-semibold text-sm">
              {loading ? 'Synthesizing India 10k Geospatial Data...' : 'Initializing Dynamic Crisis Map...'}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
