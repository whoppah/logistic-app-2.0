// frontend/src/components/PricingCard.jsx
import React from 'react';

export default function PricingCard({ partner, route, category, prices }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow space-y-4">
      <h2 className="text-xl font-semibold">{partner} Pricing</h2>
      <p className="text-gray-600">
        <strong>Route:</strong> {route}<br/>
        <strong>Category:</strong> {category}
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(prices).map(([weight, price]) => (
          <div
            key={weight}
            className="border rounded-lg p-4 flex flex-col items-center"
          >
            <span className="text-lg font-medium">{weight} kg</span>
            <span className="text-2xl font-bold mt-2">€{price.toFixed(2)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
