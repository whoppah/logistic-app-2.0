// src/components/HeatmapCard.jsx
import React, { useMemo } from 'react'
import PropTypes from 'prop-types'

// utility to map [0,1] → color ramp (light yellow → red)
function getColor(valueNorm) {
  const r = Math.floor(255 * valueNorm)
  const g = Math.floor(200 * (1 - valueNorm))
  const b = 0
  return `rgb(${r},${g},${b})`
}

export function HeatmapCard({ title, data, xKey, yKey, valueKey }) {
  // build axes
  const { xValues, yValues, matrix, maxValue } = useMemo(() => {
    const xs = Array.from(new Set(data.map(d => d[xKey]))).sort((a, b) => a - b)
    const ys = Array.from(new Set(data.map(d => d[yKey]))).sort()
    const mat = {}
    let mx = 0

    data.forEach(d => {
      const x = d[xKey], y = d[yKey], v = d[valueKey]
      mx = Math.max(mx, v)
      mat[`${y}|${x}`] = v
    })

    return { xValues: xs, yValues: ys, matrix: mat, maxValue: mx }
  }, [data, xKey, yKey, valueKey])

  return (
    <div className="bg-white p-6 rounded-xl shadow overflow-auto">
      <h2 className="text-xl font-semibold mb-4">{title}</h2>
      <table className="w-full table-auto border-collapse text-sm">
        <thead>
          <tr>
            <th className="p-2 border bg-gray-100 text-left">Category \ Weight</th>
            {xValues.map((x) => (
              <th key={x} className="p-2 border bg-gray-100 text-right">
                {x}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {yValues.map((y) => (
            <tr key={y}>
              <td className="p-2 border font-medium">{y}</td>
              {xValues.map((x) => {
                const val = matrix[`${y}|${x}`] || 0
                const norm = maxValue > 0 ? val / maxValue : 0
                return (
                  <td
                    key={x}
                    className="p-2 border text-right"
                    style={{ backgroundColor: getColor(norm) }}
                  >
                    €{val.toFixed(2)}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

HeatmapCard.propTypes = {
  title: PropTypes.string.isRequired,
  data: PropTypes.arrayOf(PropTypes.object).isRequired,
  xKey: PropTypes.string.isRequired,
  yKey: PropTypes.string.isRequired,
  valueKey: PropTypes.string.isRequired,
}
