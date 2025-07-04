// frontend/src/pages/Dashboard.jsx
import React, { useState, useCallback, useEffect } from "react";
import axios from "axios";

import PartnerSelector from "../components/PartnerSelector";
import FileUploader    from "../components/FileUploader";
import Table           from "../components/Table";

export default function Dashboard() {
  const [partner, setPartner]   = useState("brenger");
  const [files, setFiles]       = useState([]);
  const [loading, setLoading]   = useState(false);
  const [deltaSum, setDeltaSum] = useState(0);
  const [deltaOk, setDeltaOk]   = useState(false);
  const [sheetUrl, setSheetUrl] = useState("");
  const [data, setData]         = useState([]);
  const [error, setError]       = useState("");

  // Log partner + files whenever they change
  useEffect(() => {
    console.log("🔄 partner changed:", partner);
  }, [partner]);
  useEffect(() => {
    console.log("🔄 files changed:", files);
  }, [files]);

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
    console.log("🚀 Starting process for partner:", partner);

    try {
      // 1) Upload
      const form = new FormData();
      files.forEach((f) => form.append("file", f));
      console.log("📤 Sending upload FormData…", form);
      const up = await axios.post(
        `${import.meta.env.VITE_API_URL}/logistics/upload/`,
        form
      );
      console.log("📤 Upload response:", up.data);
      const { redis_key, redis_key_pdf } = up.data;

      // 2) Check delta
      const payload = {
        partner,
        redis_key: redis_key || redis_key_pdf,  // coalesce
        redis_key_pdf,
        delta_threshold: 20,
      };
      console.log("🛰️  CHECK-DELTA payload:", payload);
      const res = await axios.post(
        `${import.meta.env.VITE_API_URL}/logistics/check-delta/`,
        payload
      );
      console.log("🛰️  CHECK-DELTA response:", res.data);

      // 3) Apply result
      const {
        delta_sum,
        delta_ok,
        data: returnedData,
        sheet_url,
      } = res.data;

      console.log("✅ Parsed response fields:", {
        delta_sum,
        delta_ok,
        returnedData,
        sheet_url,
      });

      setDeltaSum(delta_sum);
      setDeltaOk(delta_ok);
      setSheetUrl(sheet_url);

      if (Array.isArray(returnedData)) {
        console.log("▶️ Setting data state to array of length:", returnedData.length);
        setData(returnedData);
      } else {
        console.error("❌ Expected returnedData to be an array but got:", returnedData);
        setData([]);
      }
    } catch (e) {
      console.error("❌ Error in handleSubmit:", e);
      setError(
        e.response?.data?.error ||
        e.response?.data?.detail ||
        e.message ||
        "Unknown error"
      );
    } finally {
      setLoading(false);
      console.log("⏹️ Loading complete");
    }
  };

  // Log data changes
  useEffect(() => {
    console.log("▶️ data state updated:", data);
  }, [data]);

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

      {/* Summary */}
      {data.length > 0 && (
        <div className="bg-white p-6 rounded-xl shadow space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-semibold">Delta Summary</h2>
              <p className={`mt-1 text-lg ${deltaOk ? "text-green-600" : "text-red-600"}`}>
                Total Delta: {deltaSum.toFixed(2)} {deltaOk ? "✅" : "⚠️"}
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
          <Table data={data} />
        </div>
      )}
    </div>
  );
}
