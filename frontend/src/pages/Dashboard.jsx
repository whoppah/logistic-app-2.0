//frontend/src/pages/Dashboard.jsx
import React, { useState } from "react";
import FileUpload from "../components/FileUpload";
import SummaryCard from "../components/SummaryCard";
import TableView from "../components/TableView";
import DeltaChart from "../components/DeltaChart";
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
        delta_threshold: 20,
      };
      const res = await axios.post(url, payload);
      setData(res.data);
    } catch (err) {
      console.error("Delta fetch failed", err);
      setError(err.response?.data?.error || "Unexpected error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Title */}
      <div>
        <h1 className="text-3xl font-bold mb-2">Logistics Invoice Dashboard</h1>
        <p className="text-gray-600">Upload invoices, calculate deltas, and extract insights</p>
      </div>

      {/* File Upload */}
      <div className="bg-white rounded-xl shadow p-6">
        <FileUpload
          partner={partner}
          setPartner={setPartner}
          onUpload={fetchDashboard}
        />
      </div>

      {/* Feedback */}
      {loading && (
        <div className="text-center text-gray-500 py-10">Processing data...</div>
      )}
      {error && (
        <div className="text-center text-red-500">{error}</div>
      )}

      {/* Insights */}
      {data && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <SummaryCard
            Delta_sum={data.delta_sum}
            delta_ok={data.delta_ok}
            Partner={partner}
            Message={data.message}
          />
          <div className="bg-white p-4 rounded-xl shadow flex items-center justify-center">
            <DeltaChart delta_sum={data.delta_sum} delta_ok={data.delta_ok} />
          </div>
        </div>
      )}

      {/* Table */}
      {data?.data && (
        <div className="bg-white rounded-xl shadow p-4">
          <h2 className="text-xl font-semibold mb-4">Invoice Delta Table</h2>
          <TableView data={data.data} />
        </div>
      )}

      {/* Google Sheet Link */}
      {data?.sheet_url && (
        <div className="text-right">
          <a
            href={data.sheet_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline"
          >
            View Report in Google Sheets
          </a>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
