// frontend/src/pages/Pricing.jsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import PartnerSelector from '../components/PartnerSelector';
import PricingCard from '../components/PricingCard';

export default function Pricing() {
  const API = import.meta.env.VITE_API_URL;
  const [partner, setPartner]     = useState('brenger');
  const [routes, setRoutes]       = useState([]);
  const [categories, setCategories] = useState([]);
  const [entries, setEntries]     = useState([]);  

  const [route, setRoute]         = useState('');
  const [category, setCategory]   = useState('');
  const [error, setError]         = useState('');

  //Load metadata when partner changes
  useEffect(() => {
    if (!partner) return;

    axios.get(`${API}/logistics/pricing/metadata/`, { params: { partner } })
      .then(res => {
        setRoutes(res.data.routes);
        setCategories(res.data.categories);
        // reset downstream selections
        setRoute('');
        setCategory('');
        setEntries([]);
        setError('');
      })
      .catch(err => {
        console.error('Metadata fetch failed', err);
        setError('Could not load metadata');
        setRoutes([]);
        setCategories([]);
      });
  }, [API, partner]);

  //When both route+category are set, fetch the prices map
  useEffect(() => {
    if (!partner || !route || !category) {
      setEntries([]);
      return;
    }

    axios.get(`${API}/logistics/pricing/`, {
      params: { partner, route, category }
    })
    .then(res => {
      // res.data.prices is { "6": 59, "7": 72, ... }
      const map = res.data.prices || {};
      const list = Object.entries(map)
        .map(([w, p]) => ({ weight: +w, price: p }))
        .sort((a, b) => a.weight - b.weight);
      setEntries(list);
      setError('');
    })
    .catch(err => {
      console.error('Price fetch failed', err);
      setError(err.response?.data?.error || 'Could not fetch prices');
      setEntries([]);
    });
  }, [API, partner, route, category]);

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-3xl font-bold">Partner Pricing Lookup</h1>

      {/*  Partner */}
      <div>
        <label className="block mb-1 font-medium">Partner</label>
        <PartnerSelector partner={partner} setPartner={setPartner} />
      </div>

      {/* only Brenger supported for now */}
      {partner === 'brenger' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Route */}
          <div>
            <label className="block mb-1 font-medium">Route</label>
            <input
              list="routes"
              value={route}
              onChange={e => setRoute(e.target.value)}
              className="border px-3 py-2 rounded w-full"
              placeholder="Type or select a route"
            />
            <datalist id="routes">
              {routes.map(r => <option key={r} value={r} />)}
            </datalist>
          </div>

          {/* Category */}
          <div>
            <label className="block mb-1 font-medium">Category</label>
            <input
              list="categories"
              value={category}
              onChange={e => setCategory(e.target.value)}
              className="border px-3 py-2 rounded w-full"
              placeholder="Type or select a category"
            />
            <datalist id="categories">
              {categories.map(c => <option key={c} value={c} />)}
            </datalist>
          </div>
        </div>
      )}

      {error && <p className="text-red-600">{error}</p>}

      {/* Pricing cards */}
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
