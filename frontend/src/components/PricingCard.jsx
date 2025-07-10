// frontend/src/components/PricingCard.jsx
import React from 'react'

export default function PricingCard({
  partner,
  route,
  category,
  weight,
  price,
}) {
  return (
    <div className="max-w-sm bg-white rounded-xl shadow p-6 space-y-4">
      <h2 className="text-xl font-semibold">{partner} Pricing</h2>

      <dl className="grid grid-cols-1 gap-y-2 text-gray-700">
        <div className="flex justify-between">
          <dt className="font-medium">Route:</dt>
          <dd>{route}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="font-medium">Category:</dt>
          <dd>{category}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="font-medium">Weight:</dt>
          <dd>{weight} kg</dd>
        </div>

        <div className="col-span-full border-t pt-4">
          <dt className="font-medium">Price:</dt>
          <dd className="mt-1 text-3xl font-bold">€{price.toFixed(2)}</dd>
        </div>
      </dl>
    </div>
  )
}
