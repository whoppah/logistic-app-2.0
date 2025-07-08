// frontend/src/pages/Dashboard.jsx
import React, { useState, useCallback, useEffect, useRef } from "react";
import axios from "axios";

import PartnerSelector from "../components/PartnerSelector";
import FileUploader from "../components/FileUploader";
import Table from "../components/Table";

export default function Dashboard() {
  const API_BASE = import.meta.env.VITE_API_URL || "";
  const [partner, setPartner] = useState("brenger");
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [deltaSum, setDeltaSum] = useState(0);
  const [deltaOk, setDeltaOk] = useState(false);
  const [sheetUrl, setSheetUrl] = useState("");
  const [data, setData] = useState([]);
  const [error, setError] = useState("");

  const [taskId, setTaskId] = useState(null);
  const pollRef = useRef(null);

  // clear polling on unmount
  useEffect(() => () => clearInterval(pollRef.current), []);

  const onFiles = useCallback((fileList) => {
    setFiles(Array.from(fileList));
  }, []);

  const startPolling = (id) => {
    pollRef.current = setInterval(async () => {
      try {
        const statusRes = await axios.get(
          `${API_BASE}/logistics/task-status/`,
          { params: { task_id: id } }
        );

        if (statusRes.data.state === "SUCCESS") {
          clearInterval(pollRef.current);
          const resultRes = await axios.get(
            `${API_BASE}/logistics/task-result/`,
            { params: { task_id: id } }
          );
          applyResult(resultRes.data);
        } else if (["FAILURE", "REVOKED"].includes(statusRes.data.state)) {
          clearInterval(pollRef.current);
          setError("Server failed to process the task.");
          setLoading(false);
        }
      } catch (e) {
        clearInterval(pollRef.current);
        setError("Error polling task status.");
        setLoading(false);
      }
    }, 2000);
  };

  const applyResult = (resData) => {
    const { delta_sum, delta_ok, sheet_url, message } = resData;
    let returnedData = Array.isArray(resData.data)
      ? resData.data
      : Array.isArray(resData.table_data)
      ? resData.table_data
      : [];

    setDeltaSum(delta_sum);
    setDeltaOk(delta_ok);
    setSheetUrl(sheet_url);

    if (returnedData.length) {
      setData(returnedData);
      setError("");
    } else {
      setData([]);
      setError(message || "No data rows returned.");
    }
    setLoading(false);
  };

  const handleSubmit = async () => {
    if (!files.length) {
      setError("Please select at least one file.");
      return;
    }

    // partner‐specific file checks
    const names = files.map((f) => f.name.toLowerCase());
    const hasPdf = names.some((n) => n.endsWith(".pdf"));
    const hasXls = names.some((n) => n.endsWith(".xls") || n.endsWith(".xlsx"));

    if (partner === "libero") {
      if (!hasPdf || !hasXls) {
        setError("Libero requires at least one PDF and one Excel file.");
        return;
      }
    } else if (["brenger", "wuunder", "transpoksi"].includes(partner)) {
      if (!hasPdf) {
        setError(`${partner} requires at least one PDF file.`);
        return;
      }
    } else if (["swdevries"].includes(partner)) {
      if (!hasXls) {
        setError(`${partner} requires at least one Excel file.`);
        return;
      }
    } else if (partner === "tadde") {
      setError("Tadde integration is not implemented yet.");
      return;
    } else if (partner === "magic_movers") {
      setError("Magic Movers needs invoices updates to compute the surcharges directly from it.");
      return;
    }

    setError("");
    setLoading(true);

    try {
      // 1️⃣ Upload
      const form = new FormData();
      files.forEach((f) => form.append("file", f));
      const up = await axios.post(`${API_BASE}/logistics/upload/`, form);
      const { redis_key, redis_key_pdf } = up.data;

      // 2️⃣ Check‐delta
      const payload = {
        partner,
        redis_key: partner === "libero" ? redis_key : redis_key || redis_key_pdf,
        redis_key_pdf,
        delta_threshold: 20,
      };
      const res = await axios.post(
        `${API_BASE}/logistics/check-delta/`,
        payload
      );

      if (res.status === 202 && res.data.task_id) {
        setTaskId(res.data.task_id);
        startPolling(res.data.task_id);
      } else {
        applyResult(res.data);
      }
    } catch (e) {
      setError(
        e.response?.data?.error ||
          e.response?.data?.detail ||
          e.message ||
          "Unknown error"
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
        className="px-6 py-3 bg-accent text-white rounded-lg hover:bg-accent/90 disabled:opacity-50"
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
                Total Delta: {deltaSum.toFixed(2)} {deltaOk ? "✅" : "🟥"}
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
