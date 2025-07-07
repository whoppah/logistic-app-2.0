// frontend/src/pages/Analytics.jsx
import { useEffect, useState } from 'react';

export default function Analytics() {
  const API_BASE = import.meta.env.VITE_API_URL || "";
  const [analyticsData, setAnalyticsData] = useState(null);

  useEffect(() => {
    async function fetchAnalytics() {
      try {
        const res = await fetch(
          `${API_BASE}/logistics/analytics/`
        );
        if (!res.ok) {
          throw new Error(`Server returned ${res.status}`);
        }
        const json = await res.json();
        setAnalyticsData(json);
      } catch (error) {
        console.error('Analytics fetch failed', error);
      }
    }

    fetchAnalytics();
  }, [API_BASE]);

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Analytics</h1>
      <p className="text-gray-600">See overall usage, delta trends, and processing history.</p>

      {!analyticsData && <p className="text-gray-500">Loading analytics...</p>}

      {analyticsData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white p-4 rounded-lg shadow">
            <h2 className="font-medium text-gray-700">Total Files Processed</h2>
            <p className="text-2xl font-bold">{analyticsData.total_files}</p>
          </div>

          <div className="bg-white p-4 rounded-lg shadow">
            <h2 className="font-medium text-gray-700">Average Delta</h2>
            <p className="text-2xl font-bold">{analyticsData.avg_delta}</p>
          </div>

          <div className="bg-white p-4 rounded-lg shadow">
            <h2 className="font-medium text-gray-700">Most Common Partner</h2>
            <p className="text-2xl font-bold">{analyticsData.top_partner}</p>
          </div>
        </div>
      )}
    </div>
  );
}
