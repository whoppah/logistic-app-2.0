//frontend/src/pages/Dashboard.jsx
import React, { useState } from "react";
import FileUpload from "../components/FileUpload";
import SummaryCard from "../components/SummaryCard";
import axios from "axios";

const Dashboard = () => {
  const [data, setData] = useState(null);
  const [partner, setPartner] = useState("brenger");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchDashboard = async (redisKey, redisKeyPdf = null) => {
    setLoading(true);
    setError("");
    try {
      const url = `${import.meta.env.VITE_API_URL}/logistics/check-delta/`;
      const payload = {
        partner,
        redis_key: redisKey,
        redis_key_pdf: redisKeyPdf,
        delta_threshold: 20, // or allow it to be dynamic
      };
      const res = await axios.post(url, payload);
      setData(res.data);
    } catch (err) {
      console.error("Failed to fetch delta check", err);
      setError(err.response?.data?.error || "Unexpected error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">Upload & Insights</h1>
      <FileUpload
        partner={partner}
        setPartner={setPartner}
        onUpload={(redisKey, redisKeyPdf) => fetchDashboard(redisKey, redisKeyPdf)}
      />
      {loading && <div className="text-center py-10">Loading...</div>}
      {error && <div className="text-red-600 py-4 text-center">{error}</div>}
      {data && (
        <SummaryCard
          delta_sum={data.delta_sum}
          delta_ok={data.delta_ok}
          sheet_url={data.sheet_url}
          message={data.message}
        />
      )}
    </div>
  );
};

export default Dashboard;
