//frontend/src/components/SummaryCard.jsx
const SummaryCard = ({ Partner, Delta_sum, delta_ok, Message }) => (
  <div className="p-6 bg-white rounded-xl shadow border-l-4 border-green-500">
    <h3 className="text-lg font-semibold mb-2">{Message}</h3>
    <p className="text-sm text-gray-600">Partner: <strong>{Partner}</strong></p>
    <p className="text-sm text-gray-600">Total Deltas: <strong>{Delta_sum}</strong></p>
    <p className="text-sm text-gray-600">OK Rows: <strong>{delta_ok}</strong></p>
  </div>
);

export default SummaryCard;
