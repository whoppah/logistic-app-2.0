// frontend/src/pages/Pricing.jsx
import React, { useEffect, useState } from 'react'
import axios from 'axios'
import PartnerSelector from '../components/PartnerSelector'
import PricingCard from '../components/PricingCard'

export default function Pricing() {
  const API = import.meta.env.VITE_API_URL
  const [partner, setPartner]   = useState('brenger')
  const [routes, setRoutes]     = useState([])
  const [categories, setCategories] = useState([])
  const [weights, setWeights]   = useState([])

  const [route, setRoute]       = useState('')
  const [category, setCategory] = useState('')
  const [weight, setWeight]     = useState('')
  const [price, setPrice]       = useState(null)
  const [error, setError]       = useState('')

  // load metadata
  useEffect(() => {
    if (partner !== 'brenger') return
    axios
      .get(`${API}/logistics/pricing/metadata/`, { params: { partner } })
      .then((res) => {
        setRoutes(res.data.routes)
        setCategories(res.data.categories)
        setWeights(res.data.weights)
      })
      .catch(() => setError('Could not load metadata'))
  }, [API, partner])

  // load price
  useEffect(() => {
    setPrice(null)
    if (!partner || !route || !category || !weight) return

    axios
      .get(`${API}/logistics/pricing/`, {
        params: { partner, route, category, weight_class: weight },
      })
      .then((res) => {
        setPrice(res.data.price)
        setError('')
      })
      .catch((e) => {
        setError(e.response?.data?.error || 'Price lookup failed')
      })
  }, [API, partner, route, category, weight])

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-3xl font-bold">Partner Pricing Lookup</h1>

      <PartnerSelector partner={partner} setPartner={setPartner} />

      {partner === 'brenger' && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* searchable inputs via datalist */}
          <div>
            <label className="block mb-1 font-medium">Route</label>
            <input
              list="routes"
              value={route}
              onChange={(e) => setRoute(e.target.value)}
              className="border px-3 py-2 rounded w-full"
            />
            <datalist id="routes">
              {routes.map((r) => (
                <option key={r} value={r} />
              ))}
            </datalist>
          </div>

          <div>
            <label className="block mb-1 font-medium">Category</label>
            <input
              list="cats"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="border px-3 py-2 rounded w-full"
            />
            <datalist id="cats">
              {categories.map((c) => (
                <option key={c} value={c} />
              ))}
            </datalist>
          </div>

          <div>
            <label className="block mb-1 font-medium">Weight class</label>
            <input
              list="wts"
              value={weight}
              onChange={(e) => setWeight(e.target.value)}
              className="border px-3 py-2 rounded w-full"
            />
            <datalist id="wts">
              {weights.map((w) => (
                <option key={w} value={w} />
              ))}
            </datalist>
          </div>
        </div>
      )}

      {error && <p className="text-red-600">{error}</p>}

      {price !== null && (
        <PricingCard
          partner={partner}
          route={route}
          category={category}
          weight={weight}
          price={price}
        />
      )}
    </div>
  )
}
