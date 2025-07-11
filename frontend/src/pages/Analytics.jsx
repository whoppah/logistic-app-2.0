// src/pages/Analytics.jsx
import { useEffect, useState } from 'react'
import StatCard from '../components/StatCard'
import { BarChartCard } from '../components/BarChartCard'
import { LineChartCard } from '../components/LineChartCard'
import { HeatmapCard }   from '../components/HeatmapCard'

export default function Analytics() {
  const API = import.meta.env.VITE_API_URL
  const [data, setData]   = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    async function fetchAnalytics() {
      try {
        const res = await fetch(`${API}/logistics/analytics/`)
        if (!res.ok) throw new Error(`Server returned ${res.status}`)
        setData(await res.json())
      } catch {
        setError('Could not load analytics')
      }
    }
    fetchAnalytics()
  }, [API])

  if (error) return <p className="text-red-600">{error}</p>
  if (!data)  return <p className="text-gray-500">Loading analytics…</p>

  const {
    total_runs,
    avg_delta_per_run,
    avg_over_per_order,
    over_per_partner,
    over_per_country,

    // new:
    trend_data,
    partners_list,
    top_routes,
    category_weight,
  } = data

  return (
    <div className="space-y-8">
      {/* ── Top‐level KPIs ───────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard title="Total Runs"      value={total_runs} />
        <StatCard
          title="Avg Δ per Run"
          value={`€${(+avg_delta_per_run).toFixed(2)}`}
        />
        <StatCard
          title="Avg Overcharge per Order"
          value={`€${(+avg_over_per_order).toFixed(2)}`}
          variant="warning"
        />
      </div>

      {/* ── Loss by Partner & Country ───────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <BarChartCard
          title="Over-charge by Partner"
          data={Object.entries(over_per_partner).map(([p, v])=>({ name:p, value:v }))}
          xKey="name"
          yKey="value"
        />
        <BarChartCard
          title="Over-charge by Country"
          data={Object.entries(over_per_country).map(([c, v])=>({ name:c, value:v }))}
          xKey="name"
          yKey="value"
        />
      </div>
      
      {/* ── New Widget 1: Time‐Series Trend ────────────────────────────── */}
      <LineChartCard
        title="Monthly Over-Charge Trend"
        data={trend_data}
        xKey="month"
        yKeys={partners_list}
      />

      {/* ── New Widget 2: Top 5 Lossy Routes ──────────────────────────── */}
      <BarChartCard
        title="Top 5 Lossy Routes (Relative)"
        data={top_routes.map(r => ({
          name: r.route,
          value: r.loss_ratio * 100,       
          total: r.total_over,
        }))}
        xKey="name"
        yKey="value"
        yFormatter={v => `${v.toFixed(1)}%`}
      />

      {/* ── New Widget 3: Category × Weight Heatmap ───────────────────── */}
      <HeatmapCard
        title="Over-Charge by Category & Weight"
        data={category_weight}
        xKey="category"
        yKey="weight"
        valueKey="over"
      />
    </div>
  )
}
