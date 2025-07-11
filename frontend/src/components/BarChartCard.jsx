//src/components/BarChartCard.jsx
import PropTypes from 'prop-types'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

export function BarChartCard({ title, data, xKey, yKey }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow">
      <h2 className="text-sm font-medium text-gray-500 mb-4">{title}</h2>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data}>
          <XAxis
            dataKey={xKey}
            tick={{ fontSize: 12 }}
            interval={0}
            angle={-45}
            textAnchor="end"
            height={60}
          />
          <YAxis
            tickFormatter={(v) => `€${v.toFixed(0)}`}
            width={60}
          />
          <Tooltip
            formatter={(v) => `€${v.toFixed(2)}`}
            cursor={{ fill: 'rgba(0,0,0,0.05)' }}
          />
          <Bar dataKey={yKey} fill="#10B981" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

BarChartCard.propTypes = {
  title: PropTypes.string.isRequired,
  data: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string,
      value: PropTypes.number,
    })
  ).isRequired,
  xKey: PropTypes.string.isRequired,
  yKey: PropTypes.string.isRequired,
}
