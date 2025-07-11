// src/pages/Analytics.jsx
import { useEffect, useState } from 'react'
import StatCard from '../components/StatCard'
import { BarChartCard }   from '../components/BarChartCard'
import { LineChartCard }  from '../components/LineChartCard'
import { HeatmapCard }    from '../components/HeatmapCard'
import InfoTooltip        from '../components/InfoTooltip'

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
    trend_data,
    partners_list,
    top_routes,
    category_weight,
  } = data

  return (
    <div className="space-y-8">

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="Total Runs"
          value={total_runs}
        />
        <StatCard
          title={
            <span className="flex items-center">
              Avg Δ per Run
              <InfoTooltip text="
                Formula: AVG(delta_sum) over all InvoiceRun records.
                i.e. (Σ delta_sum) / count(runs)
              " />
            </span>
          }
          value={`€${(+avg_delta_per_run).toFixed(2)}`}
        />
        <StatCard
          title={
            <span className="flex items-center">
              Avg Overcharge per Order
              <InfoTooltip text="
                Formula: AVG(delta) over all lines where delta>0.
                i.e. (Σ delta where delta>0) / count(lines where delta>0)
              " />
            </span>
          }
          value={`€${(+avg_over_per_order).toFixed(2)}`}
          variant="warning"
        />
      </div>

      {/* Over-charge by Partner & Country */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <h2 className="text-xl font-semibold flex items-center">
            Over-charge by Partner
            <InfoTooltip text="
              Formula: For each partner P,
                Σ(delta where delta>0 and run.partner=P)
            " />
          </h2>
          <BarChartCard
            data={Object.entries(over_per_partner)
              .map(([p, v]) => ({ name: p, value: v }))}
            xKey="name"
            yKey="value"
            yFormatter={v => `€${v.toFixed(2)}`}
          />
        </div>

        <div>
          <h2 className="text-xl font-semibold flex items-center">
            Over-charge by Country
            <InfoTooltip text="
              Formula: Group lines by buyer_country,
                Σ(delta where delta>0 and route starts with country)
            " />
          </h2>
          <BarChartCard
            data={Object.entries(over_per_country)
              .map(([c, v]) => ({ name: c, value: v }))}
            xKey="name"
            yKey="value"
            yFormatter={v => `€${v.toFixed(2)}`}
          />
        </div>
      </div>

      {/* Monthly Over-Charge Trend */}
      <div>
        <h2 className="text-xl font-semibold flex items-center">
          Monthly Over-Charge Trend
          <InfoTooltip text="
            Formula: For each month M and partner P,
              Σ(delta where delta>0 and invoice_date in M and run.partner=P)
          " />
        </h2>
        <LineChartCard
          title=""
          data={trend_data}
          xKey="month"
          yKeys={partners_list}
          yFormatter={v => `€${v.toFixed(2)}`}
        />
      </div>

      {/* Top 5 Lossy Routes */}
      <div>
        <h2 className="text-xl font-semibold flex items-center">
          Top 5 Lossy Routes (Avg per Order)
          <InfoTooltip text="
            Formula per route R:
              avg_over = (Σ delta where delta>0 and route=R) 
                         / count(lines where delta>0 and route=R)
          " />
        </h2>
        <BarChartCard
          data={top_routes.map(r => ({
            name:  r.route,
            value: r.avg_over,  
            total: r.total_over,
            orders: r.orders,
          }))}
          xKey="name"
          yKey="value"
          yFormatter={v => `€${v.toFixed(2)}`}
        />
      </div>

      {/* Heatmap: Category × Weight */}
      <div>
        <h2 className="text-xl font-semibold flex items-center">
          Over-Charge by Category & Weight
          <InfoTooltip text="
            Formula matrix cell [C, W]:
              Σ(delta where delta>0 and category=C and weight=W)
          " />
        </h2>
        <HeatmapCard
          title=""
          data={category_weight}
          xKey="category"
          yKey="weight"
          valueKey="over"
        />
      </div>
    </div>
  )
}
