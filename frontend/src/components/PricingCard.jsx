// frontend/src/components/PricingCard.jsx
import React from "react";

export default function PricingCard({ partner, route, category, weightClass, price }) {
  return (
    <div className="max-w-sm bg-white rounded-xl shadow p-6 space-y-4">
      <h2 className="text-xl font-bold lowercase">{partner} Pricing</h2>
      <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
        <div className="font-semibold">Route:</div>
        <div>{route}</div>
        <div className="font-semibold">Category:</div>
        <div>{category}</div>
        <div className="font-semibold">Weight (kg):</div>
        <div>{weightClass}</div>
      </div>
      <div className="pt-4 border-t">
        <span className="text-gray-500 text-sm">Price:</span>
        <p className="text-3xl font-semibold">${price}</p>
      </div>
    </div>
  );
}
