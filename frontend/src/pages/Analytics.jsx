//src/pages/Analytics.jsx
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

  const {
    total_files,
    avg_delta,
    top_partner,
    avg_loss_per_run,
    loss_per_partner,
    loss_per_country,
  } = data

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Analytics</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard title="Total Files Processed" value={total_files} />
        <StatCard title="Average Δ" value={`€${avg_delta.toFixed(2)}`} />
        <StatCard
          title="Avg Loss per Run"
          value={`€${avg_loss_per_run.toFixed(2)}`}
          variant="warning"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <BarChartCard
          title="Loss by Partner"
          data={Object.entries(loss_per_partner).map(([partner, loss]) => ({
            name: partner,
            value: loss,
          }))}
          xKey="name"
          yKey="value"
        />

        <BarChartCard
          title="Loss by Country"
          data={Object.entries(loss_per_country).map(
            ([country, loss]) => ({ name: country, value: loss })
          )}
          xKey="name"
          yKey="value"
        />
      </div>
    </div>
  )
}
