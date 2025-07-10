// frontend/src/pages/Pricing.jsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import PartnerSelector from '../components/PartnerSelector';
import PricingCard    from '../components/PricingCard';

export default function Pricing() {
  const API = import.meta.env.VITE_API_URL;
  const [partner,    setPartner]    = useState('brenger');
  const [routes,     setRoutes]     = useState([]);
  const [categories, setCategories] = useState([]);

  const [route,      setRoute]      = useState('');
  const [category,   setCategory]   = useState('');
  const [entries,    setEntries]    = useState([]); // [{ weight, price }]
  const [error,      setError]      = useState('');

  // Load metadata whenever partner changes
  useEffect(() => {
    if (!partner) return;
    setRoute(''); setCategory(''); setEntries([]); setError('');
    axios.get(`${API}/logistics/pricing/metadata/`, { params:{ partner } })
      .then(r => {
        setRoutes(r.data.routes);
        setCategories(r.data.categories);
      })
      .catch(() => {
        setError('Could not load metadata');
        setRoutes([]); setCategories([]);
      });
  }, [API, partner]);

  // Lookup prices whenever route+category are set
  useEffect(() => {
    if (!partner || !route || !category) {
      setEntries([]); return;
    }
    setEntries([]); setError('');
    axios.get(`${API}/logistics/pricing/`, {
      params: { partner, route, category }
    })
      .then(r => {
        const map = r.data.prices || {};
        const list = Object.entries(map)
          .map(([w,p]) => ({ weight: +w, price: p }))
          .sort((a,b)=> a.weight - b.weight);
        setEntries(list);
      })
      .catch(e => {
        setError(e.response?.data?.error || 'Lookup failed');
        setEntries([]);
      });
  }, [API, partner, route, category]);

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-3xl font-bold">Partner Pricing Lookup</h1>

      {/* Partner */}
      <div>
        <label className="block mb-1 font-medium">Partner</label>
        <PartnerSelector partner={partner} setPartner={setPartner} />
      </div>

      {/* Route & Category inputs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block mb-1 font-medium">Route</label>
          <input
            list="routes"
            placeholder="Type or pick a route"
            value={route}
            onChange={e => setRoute(e.target.value)}
            className="border px-3 py-2 rounded w-full"
          />
          <datalist id="routes">
            {routes.map(r => <option key={r} value={r} />)}
          </datalist>
        </div>
        <div>
          <label className="block mb-1 font-medium">Category</label>
          <input
            list="categories"
            placeholder="Type or pick a category"
            value={category}
            onChange={e => setCategory(e.target.value)}
            className="border px-3 py-2 rounded w-full"
          />
          <datalist id="categories">
            {categories.map(c => <option key={c} value={c} />)}
          </datalist>
        </div>
      </div>

      {error && <p className="text-red-600">{error}</p>}

      {/* Cards grid */}
      {entries.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {entries.map(({ weight, price }) => (
            <PricingCard
              key={weight}
              partner={partner}
              route={route}
              category={category}
              weight={weight}
              price={price}
            />
          ))}
        </div>
      )}
    </div>
  );
}
