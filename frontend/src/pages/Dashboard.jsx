// frontend/src/pages/Dashboard.jsx
import React, { useState, useCallback } from "react";
import axios from "axios";
import { UploadCloud } from "lucide-react";

const partnerOptions = [
  "brenger",
  "wuunder",
  "libero",
  "swdevries",
  "transpoksi",
  "magic_movers",
];

export default function Dashboard() {
  const [partner, setPartner] = useState(partnerOptions[0]);
  const [files, setFiles] = useState(null);
  const [data, setData] = useState([]);
  const [deltaSum, setDeltaSum] = useState(0);
  const [deltaOk, setDeltaOk] = useState(false);
  const [sheetUrl, setSheetUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  /** handle file selection or drop */
  const onFiles = useCallback((fileList) => {
    setFiles(Array.from(fileList));
  }, []);

  const handleDrop = (e) => {
    e.preventDefault();
    onFiles(e.dataTransfer.files);
  };

  const handleChange = (e) => {
    onFiles(e.target.files);
  };

  const uploadAndCheck = async () => {
    if (!files || files.length === 0) {
      setError("Please select at least one file.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      // 1) Upload files
      const form = new FormData();
      files.forEach((f) => form.append("file", f));
      const up = await axios.post(
        `${import.meta.env.VITE_API_URL}/logistics/upload/`,
        form
      );
      const { redis_key, redis_key_pdf } = up.data;

      // 2) Check delta
      const res = await axios.post(
        `${import.meta.env.VITE_API_URL}/logistics/check-delta/`,
        { partner, redis_key, redis_key_pdf, delta_threshold: 20 }
      );

      setData(res.data.data || []);
      setDeltaSum(res.data.delta_sum);
      setDeltaOk(res.data.delta_ok);
      setSheetUrl(res.data.sheet_url);
    } catch (e) {
      setError(e.response?.data?.error || e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ml-64 p-8 space-y-8">
      <h1 className="text-4xl font-bold text-gray-900">Invoice Dashboard</h1>
      <p className="text-gray-600">
        Upload & compare invoices for different logistics partners.
      </p>

      {/* Partner segmented control */}
      <div className="flex space-x-2">
        {partnerOptions.map((p) => (
          <button
            key={p}
            onClick={() => setPartner(p)}
            className={`px-4 py-2 rounded-lg border
              ${
                partner === p
                  ? "bg-indigo-600 text-white border-indigo-600"
                  : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
              }`}
          >
            {p.replace(/_/g, " ").toUpperCase()}
          </button>
        ))}
      </div>

      {/* Drag & drop area */}
      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        className="border-2 border-dashed border-gray-300 rounded-xl h-56 flex flex-col items-center justify-center bg-gray-50 hover:bg-gray-100 transition"
      >
        <UploadCloud className="h-12 w-12 text-gray-400" />
        <p className="mt-2 text-gray-600">Drag & drop invoice files here</p>
        <p className="text-gray-500 text-sm">.pdf, .xls, .xlsx</p>
        <input
          type="file"
          multiple
          accept=".pdf,.xls,.xlsx"
          onChange={handleChange}
          className="absolute inset-0 opacity-0 cursor-pointer"
        />
      </div>

      <button
        disabled={loading || !files}
        onClick={uploadAndCheck}
        className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
      >
        {loading ? "Processing…" : "Upload & Analyze"}
      </button>

      {error && <p className="text-red-600">{error}</p>}

      {/* Summary & link */}
      {!!data.length && (
        <div className="bg-white p-6 rounded-xl shadow space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-semibold text-gray-800">
                Delta Summary
              </h2>
              <p
                className={`mt-1 text-lg ${
                  deltaOk ? "text-green-600" : "text-red-600"
                }`}
              >
                Total Delta: {deltaSum.toFixed(2)}{" "}
                {deltaOk ? "✅" : "⚠️"}
              </p>
            </div>
            {sheetUrl && (
              <a
                href={sheetUrl}
                target="_blank"
                rel="noopener"
                className="text-indigo-600 hover:underline"
              >
                View Google Sheet →
              </a>
            )}
          </div>

          {/* Data table */}
          <div className="overflow-auto">
            <table className="min-w-full text-sm text-left">
              <thead className="bg-gray-100 text-gray-700 uppercase text-xs">
                <tr>
                  {Object.keys(data[0]).map((col) => (
                    <th key={col} className="px-4 py-2">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map((row, i) => (
                  <tr
                    key={i}
                    className={row.Delta > 0 ? "bg-green-50" : ""}
                  >
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
