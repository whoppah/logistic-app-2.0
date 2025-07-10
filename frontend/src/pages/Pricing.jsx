// frontend/src/pages/Pricing.jsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import PartnerSelector from '../components/PartnerSelector';
import PricingCard from '../components/PricingCard';

export default function Pricing() {
  const API = import.meta.env.VITE_API_URL;
  const [partner,   setPartner]   = useState('brenger');
  const [routes,    setRoutes]    = useState([]);
  const [categories, setCategories] = useState([]);

  const [route,     setRoute]     = useState('');
  const [category,  setCategory]  = useState('');
  const [prices,    setPrices]    = useState(null);
  const [error,     setError]     = useState('');

  // load metadata for partner
  useEffect(() => {
    if (partner !== 'brenger') {
      setRoutes([]); setCategories([]); 
      return;
    }
    axios.get(`${API}/logistics/pricing/metadata/`, { params: { partner } })
      .then(res => {
        setRoutes(res.data.routes);
        setCategories(res.data.categories);
      })
      .catch(e => {
        console.error(e);
        setError('Could not load metadata');
      });
  }, [partner, API]);

  // when route or category changes, fetch weight→price map
  useEffect(() => {
    setPrices(null);
    if (!route || !category) return;

    axios.get(`${API}/logistics/pricing/`, {
      params: { partner, route, category }
    })
    .then(res => {
      setPrices(res.data.prices);
      setError('');
    })
    .catch(e => {
      console.error(e);
      setError(e.response?.data?.error || 'Price lookup failed');
    });
  }, [partner, route, category, API]);

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-3xl font-bold">Partner Pricing Lookup</h1>

      {/* 1) partner selector */}
      <PartnerSelector partner={partner} setPartner={setPartner} />

      {/* 2) route + category */}
      {partner === 'brenger' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block mb-1 font-medium">Route</label>
            <select
              value={route}
              onChange={e => setRoute(e.target.value)}
              className="border px-3 py-2 rounded w-full"
            >
              <option value="">— select —</option>
              {routes.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div>
            <label className="block mb-1 font-medium">Category</label>
            <select
              value={category}
              onChange={e => setCategory(e.target.value)}
              className="border px-3 py-2 rounded w-full"
            >
              <option value="">— select —</option>
              {categories.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
        </div>
      )}

      {error && <p className="text-red-600">{error}</p>}

      {/* 3) pricing card */}
      {prices && (
        <PricingCard
          partner={partner}
          route={route}
          category={category}
          prices={prices}         
        />
      )}
    </div>
  );
}
