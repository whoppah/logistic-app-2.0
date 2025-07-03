// frontend/src/pages/Dashboard.jsx
import React, { useState } from "react";
import axios from "axios";

const partnerOptions = ["brenger", "wuunder", "libero", "swdevries"];

export default function Dashboard() {
  const [partner, setPartner] = useState("brenger");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [deltaData, setDeltaData] = useState(null);

  const handleUpload = async (e) => {
    const files = Array.from(e.target.files);
    const pdfFile = files.find((f) => f.type === "application/pdf");
    const excelFile = files.find((f) =>
      ["application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"].includes(
        f.type
      )
    );

    if (!excelFile && !pdfFile) {
      setError("Please upload a valid Excel or PDF file.");
      return;
    }

    const formData = new FormData();
    if (excelFile) formData.append("file", excelFile);
    if (pdfFile) formData.append("file", pdfFile);

    setLoading(true);
    setError("");
    setDeltaData(null);

    try {
      // Upload to backend (adapt path if needed)
      const uploadRes = await axios.post(`${import.meta.env.VITE_API_URL}/logistics/upload/`, formData);
      const { redis_key, redis_key_pdf } = uploadRes.data;

      const res = await axios.post(`${import.meta.env.VITE_API_URL}/logistics/check-delta/`, {
        partner,
        redis_key,
        redis_key_pdf,
        delta_threshold: 20,
      });

      setDeltaData(res.data);
    } catch (err) {
      console.error("❌ Delta check failed", err);
      setError(err.response?.data?.error || "Unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-800">Logistics 2.0</h1>
        <p className="text-gray-500">Upload invoice files and compare pricing data for logistics partners.</p>
      </div>

      {/* Partner Selector */}
      <div className="bg-white rounded-lg shadow p-4 w-full md:w-1/2">
        <label className="block text-sm font-medium text-gray-700 mb-1">Select Partner</label>
        <select
          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 focus:outline-none focus:ring focus:ring-indigo-500"
          value={partner}
          onChange={(e) => setPartner(e.target.value)}
        >
          {partnerOptions.map((p) => (
            <option key={p} value={p}>
              {p.charAt(0).toUpperCase() + p.slice(1)}
            </option>
          ))}
        </select>
      </div>

      {/* File Upload */}
      <div className="border-dashed border-2 border-gray-300 rounded-lg p-8 text-center bg-white shadow">
        <input
          type="file"
          multiple
          accept=".pdf,.xls,.xlsx"
          onChange={handleUpload}
          className="hidden"
          id="file-upload"
        />
        <label htmlFor="file-upload" className="cursor-pointer">
          <div className="text-gray-600">Drag & drop or click to upload invoice files</div>
          <div className="mt-2 text-sm text-gray-400">Accepted: .pdf, .xls, .xlsx</div>
        </label>
      </div>

      {/* Feedback */}
      {loading && <p className="text-gray-500">Processing files, please wait...</p>}
      {error && <p className="text-red-600">{error}</p>}

      {/* Results */}
      {deltaData && (
        <div className="space-y-6">
          <div className="bg-white p-4 rounded-lg shadow flex flex-col md:flex-row justify-between items-start md:items-center">
            <div>
              <p className="text-lg font-semibold text-gray-700">Delta Summary</p>
              <p className="text-gray-600 mt-1">Total Delta: <strong>{deltaData.delta_sum}</strong></p>
              <p className={`mt-1 text-sm ${deltaData.delta_ok ? "text-green-600" : "text-red-600"}`}>
                {deltaData.delta_ok ? "✅ Within threshold" : "⚠️ Check discrepancies"}
              </p>
            </div>
            {deltaData.sheet_url && (
              <a
                href={deltaData.sheet_url}
                target="_blank"
                rel="noreferrer"
                className="mt-4 md:mt-0 text-indigo-600 hover:underline text-sm"
              >
                View Report in Google Sheets
              </a>
            )}
          </div>

          <div className="overflow-x-auto bg-white rounded-lg shadow">
            <table className="min-w-full table-auto text-sm text-left text-gray-700">
              <thead className="bg-gray-100 text-xs uppercase">
                <tr>
                  {Object.keys(deltaData.data[0] || {}).map((col) => (
                    <th key={col} className="px-4 py-2 whitespace-nowrap">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {deltaData.data.map((row, idx) => (
                  <tr
                    key={idx}
                    className={row.Delta > 0 ? "bg-green-50" : ""}
                  >
                    {Object.values(row).map((cell, i) => (
                      <td key={i} className="px-4 py-2 border-t border-gray-100 whitespace-nowrap">
                        {typeof cell === "number" ? cell.toFixed(2) : cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

