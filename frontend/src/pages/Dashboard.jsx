// frontend/src/pages/Dashboard.jsx
import React, { useState, useCallback } from "react";
import axios from "axios";

import PartnerSelector from "../components/PartnerSelector";
import FileUploader    from "../components/FileUploader";

export default function Dashboard() {
  const [partner, setPartner] = useState("brenger");
  const [files, setFiles]     = useState([]);

  const [loading, setLoading] = useState(false);
  const [deltaSum, setDeltaSum] = useState(0);
  const [deltaOk, setDeltaOk]   = useState(false);
  const [sheetUrl, setSheetUrl] = useState("");
  const [data, setData]         = useState([]);
  const [error, setError]       = useState("");

  const onFiles = useCallback((fileList) => {
    setFiles(Array.from(fileList));
  }, []);

  const handleSubmit = async () => {
    if (!files.length) {
      setError("Please select at least one file.");
      return;
    }
    setError("");
    setLoading(true);

    try {
      // 1️⃣ Upload
      const form = new FormData();
      files.forEach((f) => form.append("file", f));
      const up = await axios.post(
        `${import.meta.env.VITE_API_URL}/logistics/upload/`,
        form
      );
      const { redis_key, redis_key_pdf } = up.data;

      // 2️⃣ Check delta (synchronous)
      const payload = {
        partner,
        redis_key: redis_key || redis_key_pdf,
        redis_key_pdf,
        delta_threshold: 20,
      };
      const res = await axios.post(
        `${import.meta.env.VITE_API_URL}/logistics/check-delta/`,
        payload
      );

      // 3️⃣ Apply results
      const { delta_sum, delta_ok, data, sheet_url } = res.data;
      setDeltaSum(delta_sum);
      setDeltaOk(delta_ok);
      setSheetUrl(sheet_url);
      setData(data);
    } catch (e) {
      setError(
        e.response?.data?.error ||
        e.response?.data?.detail ||
        e.message
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ml-64 p-8 space-y-8">
      <h1 className="text-4xl font-bold">Invoice Dashboard</h1>

      <PartnerSelector partner={partner} setPartner={setPartner} />

      <FileUploader onFiles={onFiles} files={files} />

      <button
        onClick={handleSubmit}
        disabled={loading}
        className="px-6 py-3 bg-indigo-600 text-white rounded-lg disabled:opacity-50"
      >
        {loading ? "Processing…" : "Upload & Analyze"}
      </button>

      {error && <p className="text-red-600">{error}</p>}

      {!!data.length && (
        <div className="bg-white p-6 rounded-xl shadow space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-semibold">Delta Summary</h2>
              <p className={`mt-1 text-lg ${deltaOk ? "text-green-600" : "text-red-600"}`}>
                Total Delta: {deltaSum.toFixed(2)} {deltaOk ? "✅" : "⚠️"}
              </p>
            </div>
            {sheetUrl && (
              <a href={sheetUrl} target="_blank" rel="noopener" className="text-indigo-600 hover:underline">
                View Google Sheet →
              </a>
            )}
          </div>
          <div className="overflow-auto">
            <table className="min-w-full text-sm text-left">
              <thead className="bg-gray-100 uppercase text-xs">
                <tr>
                  {Object.keys(data[0]).map((col) => (
                    <th key={col} className="px-4 py-2">{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map((row, i) => (
                  <tr key={i} className={row.Delta > 0 ? "bg-green-50" : ""}>
                    {Object.values(row).map((val, j) => (
                      <td key={j} className="px-4 py-2 border-t">
                        {typeof val === "number" ? val.toFixed(2) : val}
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
