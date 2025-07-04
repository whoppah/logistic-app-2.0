// frontend/src/pages/Dashboard.jsx
import React, { useState, useCallback, useEffect, useRef } from "react";
import axios from "axios";

import PartnerSelector from "../components/PartnerSelector";
import FileUploader from "../components/FileUploader";
import Table from "../components/Table";

export default function Dashboard() {
  const [partner, setPartner]   = useState("brenger");
  const [files, setFiles]       = useState([]);
  const [loading, setLoading]   = useState(false);
  const [deltaSum, setDeltaSum] = useState(0);
  const [deltaOk, setDeltaOk]   = useState(false);
  const [sheetUrl, setSheetUrl] = useState("");
  const [data, setData]         = useState([]);
  const [error, setError]       = useState("");

  const [taskId, setTaskId]     = useState(null);
  const pollRef = useRef(null);

  useEffect(() => {
    return () => clearInterval(pollRef.current);
  }, []);

  const onFiles = useCallback((fileList) => {
    setFiles(Array.from(fileList));
  }, []);

  const startPolling = (id) => {
    pollRef.current = setInterval(async () => {
      try {
        const statusRes = await axios.get(
          `/api/logistics/task-status/`,
          { params: { task_id: id } }
        );
        console.log("🕵️ task-status:", statusRes.data);
        if (statusRes.data.status === "success") {
          clearInterval(pollRef.current);

          const resultRes = await axios.get(
            `/api/logistics/task-result/`,
            { params: { task_id: id } }
          );
          console.log("✅ task-result:", resultRes.data);
          applyResult(resultRes.data);
        }
        else if (statusRes.data.status === "failure") {
          clearInterval(pollRef.current);
          setError("Server failed to process the task.");
          setLoading(false);
        }
      } catch (e) {
        console.error("Polling error:", e);
        clearInterval(pollRef.current);
        setError("Error polling task status.");
        setLoading(false);
      }
    }, 2000);
  };

  const applyResult = (resData) => {
   
    console.log("🔧 applyResult payload:", resData);
    const { delta_sum, delta_ok, sheet_url } = resData;
    let returnedData = [];
    if (Array.isArray(resData.data)) returnedData = resData.data;
    else if (Array.isArray(resData.table_data)) returnedData = resData.table_data;

    setDeltaSum(delta_sum);
    setDeltaOk(delta_ok);
    setSheetUrl(sheet_url);

    if (returnedData.length) {
      setData(returnedData);
      setError("");
    } else {
      setData([]);
      setError(resData.message || "No data rows returned from task-result.");
    }
    setLoading(false);
  };

  const handleSubmit = async () => {
    if (!files.length) {
      setError("Please select at least one file.");
      return;
    }
    setError("");
    setLoading(true);
    console.log("🚀 Starting process for partner:", partner);

    try {
      // Upload
      const form = new FormData();
      files.forEach((f) => form.append("file", f));
      console.log("📤 Uploading files…");
      const up = await axios.post("/api/logistics/upload/", form);
      console.log("📤 upload response:", up.data);
      const { redis_key, redis_key_pdf } = up.data;

      // Check-delta
      const payload = {
        partner,
        redis_key: redis_key || redis_key_pdf,
        redis_key_pdf,
        delta_threshold: 20,
      };
      console.log("🛰️ check-delta payload:", payload);

      const res = await axios.post("/api/logistics/check-delta/", payload);
      console.log("🛰️ check-delta response code:", res.status, res.data);

      if (res.status === 202 && res.data.task_id) {
        // async case: start polling
        setTaskId(res.data.task_id);
        startPolling(res.data.task_id);
      } else {
        // sync case: got immediate result in 200
        applyResult(res.data);
      }
    } catch (e) {
      console.error("❌ handleSubmit error:", e);
      setError(
        e.response?.data?.error ||
        e.response?.data?.detail ||
        e.message ||
        "Unknown error on check-delta"
      );
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

      {error && <p className="text-red-600 whitespace-pre-wrap">{error}</p>}

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
          <Table data={data} />
        </div>
      )}
    </div>
  );
}
