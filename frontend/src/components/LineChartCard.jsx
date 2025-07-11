// src/components/LineChartCard.jsx
import React from 'react'
import PropTypes from 'prop-types'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from 'recharts'

export function LineChartCard({ title, data, xKey, yKeys }) {
  // auto‐assign colors
  const colors = ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6']
  
  return (
    <div className="bg-white p-6 rounded-xl shadow">
      <h2 className="text-xl font-semibold mb-4">{title}</h2>
      <div style={{ width: '100%', height: 300 }}>
        <ResponsiveContainer>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey={xKey}
              tick={{ fontSize: 12 }}
              padding={{ left: 10, right: 10 }}
            />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip formatter={(value) => `€${value.toFixed(2)}`} />
            <Legend verticalAlign="top" height={36} />
            {yKeys.map((key, idx) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={colors[idx % colors.length]}
                dot={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

LineChartCard.propTypes = {
  title: PropTypes.string.isRequired,
  data: PropTypes.arrayOf(PropTypes.object).isRequired,
  xKey: PropTypes.string.isRequired,
  yKeys: PropTypes.arrayOf(PropTypes.string).isRequired,
}
