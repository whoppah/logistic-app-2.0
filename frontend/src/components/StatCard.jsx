//src/frontend/components/StatCard.jsx
import PropTypes from 'prop-types'

export default function StatCard({ title, value, variant = 'neutral' }) {
  const colorClass =
    variant === 'warning' ? 'text-red-600' : 'text-gray-800'

  return (
    <div className="bg-white p-6 rounded-xl shadow">
      <h2 className="text-sm font-medium text-gray-500">{title}</h2>
      <p className={`mt-2 text-2xl font-bold ${colorClass}`}>{value}</p>
    </div>
  )
}

StatCard.propTypes = {
  title: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  variant: PropTypes.oneOf(['neutral', 'warning']),
}
