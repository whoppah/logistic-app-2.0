// frontend/src/pages/Pricing.jsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';

import PartnerSelector from '../components/PartnerSelector';
import PricingCard    from '../components/PricingCard';

export default function Pricing() {
  const API = import.meta.env.VITE_API_URL || "";
  const [partner,   setPartner]   = useState('brenger');
  const [routes,    setRoutes]    = useState([]);
  const [categories, setCategories] = useState([]);
  const [weights,   setWeights]   = useState([]);

  const [route,     setRoute]     = useState('');
  const [category,  setCategory]  = useState('');
  const [weight,    setWeight]    = useState('');
  const [price,     setPrice]     = useState(null);
  const [error,     setError]     = useState('');

  // load metadata when partner changes
  useEffect(() => {
    async function loadMetadata() {
      if (partner !== 'brenger') {
        setRoutes([]); setCategories([]); setWeights([]);
        return;
      }
      try {
        const res = await axios.get(`${API}/logistics/pricing/metadata/`, { params: { partner } });
        setRoutes(res.data.routes);
        setCategories(res.data.categories);
        setWeights(res.data.weights);
        setError('');
      } catch (e) {
        console.error('Metadata fetch failed', e);
        setError(`Could not load metadata for ${partner}`);
      }
    }
    loadMetadata();
  }, [API, partner]);

  // fetch price when everything is selected
  useEffect(() => {
    async function loadPrice() {
      setPrice(null);
      if (!partner || !route || !category || !weight) return;
      try {
        const res = await axios.get(`${API}/logistics/pricing/`, {
          params: { partner, route, category, weight_class: weight }
        });
        setPrice(res.data.price);
        setError('');
      } catch (e) {
        console.error('Price fetch failed', e);
        setError('Could not fetch price');
      }
    }
    loadPrice();
  }, [API, partner, route, category, weight]);

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-3xl font-bold">Partner Pricing Lookup</h1>

      {/* Partner selector */}
      <div>
        <label className="block mb-1 font-medium">Partner</label>
        <PartnerSelector partner={partner} setPartner={setPartner} />
      </div>

      {partner === 'brenger' && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Route */}
          <div>
            <label className="block mb-1 font-medium">Route</label>
            <input
              list="routes-list"
              value={route}
              onChange={e => setRoute(e.target.value)}
              placeholder="Type or select a route"
              className="border px-3 py-2 rounded w-full"
            />
            <datalist id="routes-list">
              {routes.map(r => <option key={r} value={r} />)}
            </datalist>
          </div>

          {/* Category */}
          <div>
            <label className="block mb-1 font-medium">Category</label>
            <input
              list="categories-list"
              value={category}
              onChange={e => setCategory(e.target.value)}
              placeholder="Type or select a category"
              className="border px-3 py-2 rounded w-full"
            />
            <datalist id="categories-list">
              {categories.map(c => <option key={c} value={c} />)}
            </datalist>
          </div>

          {/* Weight class */}
          <div>
            <label className="block mb-1 font-medium">Weight class</label>
            <input
              list="weights-list"
              value={weight}
              onChange={e => setWeight(e.target.value)}
              placeholder="Type or select a weight"
              className="border px-3 py-2 rounded w-full"
            />
            <datalist id="weights-list">
              {weights.map(w => <option key={w} value={w} />)}
            </datalist>
          </div>
        </div>
      )}

      {error && <p className="text-red-600">{error}</p>}

      {price !== null && (
        <div className="mt-6">
          <PricingCard
            partner={partner}
            route={route}
            category={category}
            weightClass={weight}
            price={price}
          />
        </div>
      )}
    </div>
  );
}
