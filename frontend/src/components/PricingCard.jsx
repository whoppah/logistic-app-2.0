//frontend/src/components/PricingCard.jsx
import React, { useState, useEffect } from "react";
import axios from "axios";

export default function PricingCard({ partner }) {
  const API = import.meta.env.VITE_API_URL;
  const [routes,    setRoutes   ] = useState([]);
  const [cats,      setCats     ] = useState([]);
  const [weights,   setWeights  ] = useState([]);
  const [route,     setRoute    ] = useState("");
  const [category,  setCategory ] = useState("");
  const [weight,    setWeight   ] = useState("");
  const [price,     setPrice    ] = useState(null);
  const [error,     setError    ] = useState("");

  // 1) on mount, fetch the entire JSON to populate selects
  useEffect(() => {
    (async () => {
      try {
        const resp = await fetch(`${API}/logistics/pricing/?partner=${partner}`)
        const j    = await resp.json();
        
        setRoutes(   Object.keys(j).filter(k=> k.match(/^[A-Z]{2}-[A-Z]{2}$/)) );
        setCats(     Object.values(j["CMS category"]) );
        setWeights(  Object.values(j["Weightclass"]).map(w=> w.toFixed(2)) );
      } catch (e) {
        console.error(e);
      }
    })();
  }, [partner]);

  // 2) whenever all three are set, lookup the price
  useEffect(() => {
    if (!route||!category||!weight) return;
    (async () => {
      try {
        const resp = await axios.get(`${API}/logistics/pricing/`, {
          params: { partner, route, category, weight }
        });
        setPrice(resp.data.price);
        setError("");
      } catch (e) {
        setPrice(null);
        setError(e.response?.data?.error || "Lookup failed");
      }
    })();
  }, [partner, route, category, weight]);

  return (
    <div className="p-4 bg-white rounded-lg shadow-md space-y-4 w-full max-w-sm">
      <h3 className="text-lg font-bold">{partner} Pricing</h3>

      <div>
        <label className="block text-sm font-medium">Route</label>
        <select
          value={route}
          onChange={e=> setRoute(e.target.value)}
          className="mt-1 block w-full rounded border px-3 py-2"
        >
          <option value="">— select —</option>
          {routes.map(r => <option key={r} value={r}>{r}</option>)}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium">Category</label>
        <select
          value={category}
          onChange={e=> setCategory(e.target.value)}
          className="mt-1 block w-full rounded border px-3 py-2"
        >
          <option value="">— select —</option>
          {cats.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium">Weight (kg)</label>
        <select
          value={weight}
          onChange={e=> setWeight(e.target.value)}
          className="mt-1 block w-full rounded border px-3 py-2"
        >
          <option value="">— select —</option>
          {weights.map(w => <option key={w} value={w}>{w}</option>)}
        </select>
      </div>

      <div className="pt-2 border-t">
        {price != null ? (
          <p className="text-2xl font-semibold">
            €{price.toFixed(2)}
          </p>
        ) : error ? (
          <p className="text-red-500 text-sm">{error}</p>
        ) : (
          <p className="text-gray-500 text-sm">Select all fields</p>
        )}
      </div>
    </div>
  );
}
