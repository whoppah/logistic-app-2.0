//frontend/src/components/SummaryCard.jsx
const SummaryCard = ({ Partner, Delta_sum, Message }) => (
  <div className="p-4 bg-white rounded shadow mb-4 border-l-4 border-green-500">
    <strong>{Message}</strong><br />
    <span className="text-sm text-gray-600">Partner: {Partner} | Delta sum: {Delta_sum}</span>
  </div>
);

export default SummaryCard;
