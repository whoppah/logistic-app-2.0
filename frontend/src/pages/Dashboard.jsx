// frontend/src/pages/Dashboard.jsx
import React, { useState, useCallback, useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import axios from "axios";

import PartnerSelector from "../components/PartnerSelector";
import FileUploader   from "../components/FileUploader";
import Table          from "../components/Table";

export default function Dashboard() {
  const API_BASE     = import.meta.env.VITE_API_URL;
  const { state }    = useLocation();
  const initPartner  = state?.partner;
  const initFileUrls = state?.fileUrls || [];

  const [partner,   setPartner]  = useState(initPartner || "brenger");
  const [files,     setFiles]    = useState([]);
  const [loading,   setLoading]  = useState(false);
  const [deltaSum,  setDeltaSum] = useState(0);
  const [deltaOk,   setDeltaOk]  = useState(false);
  const [sheetUrl,  setSheetUrl] = useState("");
  const [data,      setData]     = useState([]);
  const [error,     setError]    = useState("");
  const [taskId,    setTaskId]   = useState(null);
  const pollRef = useRef(null);

  // Cleanup polling on unmount
  useEffect(() => () => clearInterval(pollRef.current), []);

  // If arrived via Slack “Analyze” button, download & auto-submit
  useEffect(() => {
    if (initPartner && initFileUrls.length) {
      (async () => {
        try {
          // 1) proxy-download each Slack file through your backend
          const downloaded = await Promise.all(
            initFileUrls.map(async (url, idx) => {
              const proxyUrl = `${API_BASE}/logistics/slack/download/?file_url=${encodeURIComponent(url)}`;
              const resp = await fetch(proxyUrl);
              if (!resp.ok) throw new Error("Download failed");
              const blob = await resp.blob();
              const ext  = blob.type === "application/pdf" ? ".pdf" : ".xlsx";
              return new File([blob], `${initPartner}_${idx}${ext}`, { type: blob.type });
            })
          );

          // 2) stash them into state and kick off the normal pipeline
          setFiles(downloaded);
          setPartner(initPartner);
          setTimeout(() => handleSubmit(downloaded, initPartner), 100);
        } catch (e) {
          console.error("Prefetch error:", e);
          setError("Couldn’t fetch invoice files from Slack.");
        }
      })();
    }
  }, []); // run once

  const onFiles = useCallback((fileList) => setFiles(Array.from(fileList)), []);

  const startPolling = (id) => {
    pollRef.current = setInterval(async () => {
      try {
        const { data: status } = await axios.get(
          `${API_BASE}/logistics/task-status/`,
          { params: { task_id: id } }
        );
        if (status.state === "SUCCESS") {
          clearInterval(pollRef.current);
          const { data: result } = await axios.get(
            `${API_BASE}/logistics/task-result/`,
            { params: { task_id: id } }
          );
          applyResult(result);
        } else if (["FAILURE","REVOKED"].includes(status.state)) {
          clearInterval(pollRef.current);
          setError("Server failed to process the task.");
          setLoading(false);
        }
      } catch {
        clearInterval(pollRef.current);
        setError("Error polling task status.");
        setLoading(false);
      }
    }, 2000);
  };

  const applyResult = (resData) => {
    const { delta_sum, delta_ok, sheet_url, message } = resData;
    const returnedData = Array.isArray(resData.data)
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

  // Accept optional overrideFiles & overridePartner for auto-submit
  const handleSubmit = async (overrideFiles, overridePartner) => {
    const useFiles   = overrideFiles   || files;
    const usePartner = overridePartner || partner;

    if (!useFiles.length) {
      setError("Please select at least one file.");
      return;
    }
    setPartner(usePartner);
    setError("");
    setLoading(true);

    // Partner-specific checks (as before)…
    const names = useFiles.map((f) => f.name.toLowerCase());
    const hasPdf = names.some((n) => n.endsWith(".pdf"));
    const hasXls = names.some((n) => /\.(xls|xlsx)$/.test(n));

    if (usePartner === "libero" && (!hasPdf || !hasXls)) {
      setError("Libero requires both PDF and Excel.");
      setLoading(false);
      return;
    }
    if (["brenger","wuunder","transpoksi"].includes(usePartner) && !hasPdf) {
      setError(`${usePartner} requires a PDF file.`);
      setLoading(false);
      return;
    }
    if (usePartner === "swdevries" && !hasXls) {
      setError("Sw De Vries requires an Excel file.");
      setLoading(false);
      return;
    }
    // …and so on for the rest…

    try {
      // 1️⃣ Upload to Redis
      const form = new FormData();
      useFiles.forEach((f) => form.append("file", f));
      const up = await axios.post(`${API_BASE}/logistics/upload/`, form);
      const { redis_key, redis_key_pdf } = up.data;

      // 2️⃣ Launch Delta chain
      const payload = {
        partner:         usePartner,
        redis_key:       usePartner === "libero" ? redis_key : redis_key || redis_key_pdf,
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
      <FileUploader   onFiles={onFiles} files={files} />
      <button
        onClick={() => handleSubmit()}
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
