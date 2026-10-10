import { useEffect, useRef, useState } from 'react'
import { MapPin, Navigation, Compass, Layers, ShieldCheck, Clock, ExternalLink } from 'lucide-react'

const getTrustColor = (score) => {
  if (score >= 75) return '#10b981' // emerald
  if (score >= 40) return '#f59e0b' // amber
  return '#ef4444' // red
}

export default function SearchResultsMap({
  userLocation,
  results = [],
  selectedHospital = null,
  onSelectHospital = () => {},
}) {
  const mapRef = useRef(null)
  const mapInstance = useRef(null)
  const markersRef = useRef([])
  const pathRef = useRef(null)
  const [mapReady, setMapReady] = useState(false)

  // Initialize Leaflet Map
  useEffect(() => {
    if (typeof window === 'undefined' || mapInstance.current) return

    import('leaflet').then((L) => {
      const defaultCenter = userLocation?.lat && userLocation?.lng
        ? [userLocation.lat, userLocation.lng]
        : [25.6120, 85.1580]

      const map = L.map(mapRef.current, {
        center: defaultCenter,
        zoom: 10,
        zoomControl: true,
      })

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap &bull; MedMap Geospatial Engine',
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

  // Render User Location and Recommended Hospital Markers
  useEffect(() => {
    if (!mapReady || !mapInstance.current) return

    import('leaflet').then((L) => {
      // Clear existing markers & path
      markersRef.current.forEach((m) => m.remove())
      markersRef.current = []
      if (pathRef.current) {
        pathRef.current.remove()
        pathRef.current = null
      }

      const bounds = []

      // 1. Render User Location Marker
      if (userLocation && userLocation.lat && userLocation.lng) {
        const uLat = Number(userLocation.lat)
        const uLng = Number(userLocation.lng)
        bounds.push([uLat, uLng])

        const userIcon = L.divIcon({
          className: '',
          html: `<div style="
            position: relative;
            width: 22px; height: 22px;
          ">
            <div style="
              position: absolute; inset: -4px;
              border-radius: 50%;
              background: rgba(14, 165, 233, 0.35);
              animation: ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;
            "></div>
            <div style="
              width: 22px; height: 22px; border-radius: 50%;
              background: #0284c7; border: 3px solid #ffffff;
              box-shadow: 0 0 12px rgba(2, 132, 199, 0.6), 0 3px 6px rgba(0,0,0,0.3);
              display: flex; align-items: center; justify-content: center;
              color: white; font-size: 11px; font-weight: bold;
            ">
              ★
            </div>
          </div>`,
          iconSize: [22, 22],
          iconAnchor: [11, 11],
        })

        const userMarker = L.marker([uLat, uLng], { icon: userIcon, zIndexOffset: 1000 })
          .addTo(mapInstance.current)

        userMarker.bindTooltip(
          `<div style="font-family: sans-serif; font-size: 12px; padding: 3px;">
            <strong style="color: #0284c7;">📍 Your Location (${userLocation.source?.toUpperCase() || 'LOCKED'})</strong><br/>
            <span>${userLocation.address || 'User Real-time Coordinates'}</span><br/>
            <span style="font-size: 10px; color: #64748b;">${uLat.toFixed(4)}°N, ${uLng.toFixed(4)}°E</span>
          </div>`,
          { direction: 'top', permanent: false, offset: [0, -12] }
        )

        markersRef.current.push(userMarker)
      }

      // 2. Render Hospital Markers from Search Results
      results.forEach((hosp, idx) => {
        const hLat = hosp.lat ?? hosp.latitude
        const hLng = hosp.lng ?? hosp.longitude
        if (!hLat || !hLng) return

        bounds.push([hLat, hLng])
        const color = getTrustColor(hosp.trust_score || 50)
        const rank = idx + 1
        const isBestFit = rank === 1
        const isSelected = selectedHospital && selectedHospital.id === hosp.id

        const hospIcon = L.divIcon({
          className: '',
          html: `<div style="
            width: ${isBestFit ? '28px' : '22px'};
            height: ${isBestFit ? '28px' : '22px'};
            border-radius: 50%;
            background: ${color};
            border: ${isSelected ? '3px solid #0f172a' : '2.5px solid #ffffff'};
            box-shadow: 0 0 ${isBestFit ? '14px' : '8px'} ${color}aa, 0 3px 6px rgba(0,0,0,0.35);
            display: flex; align-items: center; justify-content: center;
            color: #ffffff; font-weight: 800;
            font-size: ${isBestFit ? '12px' : '10px'};
            font-family: sans-serif;
            cursor: pointer;
            transition: transform 0.15s ease;
          ">
            ${rank}
          </div>`,
          iconSize: [isBestFit ? 28 : 22, isBestFit ? 28 : 22],
          iconAnchor: [isBestFit ? 14 : 11, isBestFit ? 14 : 11],
        })

        const marker = L.marker([hLat, hLng], { icon: hospIcon, zIndexOffset: isBestFit ? 900 : 500 })
          .addTo(mapInstance.current)
          .on('click', () => {
            onSelectHospital(hosp)
          })

        const distStr = hosp.distance_km ? `${hosp.distance_km} km` : 'Near target area'
        const travelStr = hosp.travel_time_min ? ` (~${hosp.travel_time_min} mins)` : ''

        marker.bindTooltip(
          `<div style="font-family: sans-serif; font-size: 11px; max-width: 240px; padding: 4px;">
            <div style="font-weight: 800; font-size: 12px; margin-bottom: 2px;">
              #${rank} ${hosp.name}
            </div>
            <div style="color: ${color}; font-weight: 700; margin-bottom: 2px;">
              Trust Score: ${hosp.trust_score}/100 &bull; ${hosp.trust_tier?.toUpperCase() || ''}
            </div>
            <div style="color: #334155; margin-bottom: 2px;">
              📍 <strong>${distStr}</strong>${travelStr} from chosen location
            </div>
            <div style="color: #64748b; font-size: 10px;">
              ${hosp.city || hosp.district}, ${hosp.state} &bull; ${hosp.validator_verdict || 'PASSED'}
            </div>
          </div>`,
          { direction: 'top', offset: [0, -10] }
        )

        markersRef.current.push(marker)
      })

      // 3. Connect Best Fit (Rank 1) to User with dashed trajectory
      if (userLocation && userLocation.lat && userLocation.lng && results.length > 0) {
        const topHosp = results[0]
        const topLat = topHosp.lat ?? topHosp.latitude
        const topLng = topHosp.lng ?? topHosp.longitude

        if (topLat && topLng) {
          pathRef.current = L.polyline(
            [
              [userLocation.lat, userLocation.lng],
              [topLat, topLng],
            ],
            {
              color: '#0284c7',
              weight: 2.5,
              opacity: 0.8,
              dashArray: '6, 6',
            }
          ).addTo(mapInstance.current)
        }
      }

      // Auto fit map view to enclose user and hospitals
      if (bounds.length > 1) {
        mapInstance.current.fitBounds(bounds, { padding: [40, 40], maxZoom: 13 })
      } else if (bounds.length === 1) {
        mapInstance.current.setView(bounds[0], 11)
      }
    })
  }, [mapReady, userLocation, results, selectedHospital, onSelectHospital])

  // Center on selected hospital when clicked
  useEffect(() => {
    if (!mapReady || !mapInstance.current || !selectedHospital) return
    const lat = selectedHospital.lat ?? selectedHospital.latitude
    const lng = selectedHospital.lng ?? selectedHospital.longitude
    if (lat && lng) {
      mapInstance.current.flyTo([lat, lng], 13, { duration: 1.0 })
    }
  }, [selectedHospital, mapReady])

  const topMatch = results[0]

  return (
    <div className="relative w-full h-[360px] md:h-[420px] rounded-2xl overflow-hidden border border-slate-200 shadow-sm bg-slate-50">
      <div ref={mapRef} className="w-full h-full" />

      {/* Top Overlay Badge */}
      <div className="absolute top-3 left-3 z-[1000] flex items-center gap-2 flex-wrap">
        <div className="bg-white/95 backdrop-blur-xs border border-slate-200 px-3 py-1.5 rounded-xl shadow-xs text-xs font-semibold text-slate-800 flex items-center gap-2">
          <Navigation className="w-3.5 h-3.5 text-sky-600 animate-pulse" />
          <span>
            {userLocation?.address || 'Target Location Locked'}
          </span>
          <span className="text-[10px] font-mono bg-sky-100 text-sky-800 px-1.5 py-0.5 rounded">
            {userLocation?.source?.toUpperCase() || 'GPS'}
          </span>
        </div>

        {topMatch && (
          <div className="hidden sm:flex bg-emerald-600/95 backdrop-blur-xs text-white px-3 py-1.5 rounded-xl shadow-xs text-xs font-semibold items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Best Fit: #{1} {topMatch.name.slice(0, 26)}…</span>
            <span className="text-[10px] bg-white/20 px-1 rounded font-mono">
              {topMatch.distance_km ? `${topMatch.distance_km}km` : 'Nearby'}
            </span>
          </div>
        )}
      </div>

      {/* Bottom Map Legend */}
      <div className="absolute bottom-3 right-3 z-[1000] bg-white/90 backdrop-blur-xs border border-slate-200 rounded-xl px-2.5 py-1.5 text-[10px] text-slate-600 flex items-center gap-3 shadow-xs">
        <div className="flex items-center gap-1">
          <div className="w-2.5 h-2.5 rounded-full bg-sky-600 border border-white"></div>
          <span>You</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 border border-white"></div>
          <span>High Trust (&ge;75)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2.5 h-2.5 rounded-full bg-amber-500 border border-white"></div>
          <span>Medium</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2.5 h-2.5 rounded-full bg-red-500 border border-white"></div>
          <span>Low/Flagged</span>
        </div>
      </div>
    </div>
  )
}
