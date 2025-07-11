// src/pages/Analytics.jsx
import { useEffect, useState } from 'react'
import StatCard from '../components/StatCard'
import { BarChartCard } from '../components/BarChartCard'

export default function Analytics() {
  const API = import.meta.env.VITE_API_URL
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    async function fetchAnalytics() {
      try {
        const res = await fetch(`${API}/logistics/analytics/`)
        if (!res.ok) throw new Error(`Server returned ${res.status}`)
        const json = await res.json()
        setData(json)
      } catch (err) {
        console.error(err)
        setError('Could not load analytics')
      }
    }
    fetchAnalytics()
  }, [API])

  if (error) {
    return <p className="text-red-600">{error}</p>
  }
  if (!data) {
    return <p className="text-gray-500">Loading analytics…</p>
  }

  // Destructure with defaults matching the new API fields
  const {
    total_runs            = 0,
    avg_delta_per_run     = 0,
    top_partner           = '',
    avg_over_per_order    = 0,
    over_per_partner      = {},
    over_per_country      = {},
  } = data

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Analytics</h1>

      {/* KPI Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="Total Runs Processed"
          value={typeof total_runs === 'number' ? total_runs : 0}
        />
        <StatCard
          title="Average Δ per Run"
          value={`€${(+avg_delta_per_run || 0).toFixed(2)}`}
        />
        <StatCard
          title="Avg Over‐charge per Order"
          value={`€${(+avg_over_per_order || 0).toFixed(2)}`}
          variant="warning"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {Object.keys(over_per_partner).length > 0 && (
          <BarChartCard
            title="Over-charge by Partner"
            data={Object.entries(over_per_partner).map(
              ([partner, over]) => ({
                name: partner,
                value: typeof over === 'number' ? over : 0,
              })
            )}
            xKey="name"
            yKey="value"
          />
        )}

        {Object.keys(over_per_country).length > 0 && (
          <BarChartCard
            title="Over-charge by Country"
            data={Object.entries(over_per_country).map(
              ([country, over]) => ({
                name: country,
                value: typeof over === 'number' ? over : 0,
              })
            )}
            xKey="name"
            yKey="value"
          />
        )}
      </div>
    </div>
  )
}
