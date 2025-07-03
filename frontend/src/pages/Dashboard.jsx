// frontend/src/pages/Dashboard.jsx
import React, { useState, useCallback, useEffect, useRef } from "react";
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

  // Task / result state
  const [taskId, setTaskId] = useState(null);
  const [polling, setPolling] = useState(false);
  const [deltaSum, setDeltaSum] = useState(0);
  const [deltaOk, setDeltaOk] = useState(false);
  const [sheetUrl, setSheetUrl] = useState("");
  const [data, setData] = useState([]);
  const [error, setError] = useState("");

  const pollRef = useRef(null);

  const onFiles = useCallback((fileList) => {
    setFiles(Array.from(fileList));
  }, []);

  const handleDrop = (e) => {
    e.preventDefault();
    onFiles(e.dataTransfer.files);
  };
  const handleChange = (e) => onFiles(e.target.files);

  const startProcess = async () => {
    if (!files || files.length === 0) {
      setError("Please select at least one file.");
      return;
    }

    setError("");
    try {
      // 1) Upload to /logistics/upload/
      const form = new FormData();
      files.forEach((f) => form.append("file", f));
      const up = await axios.post(
        `${import.meta.env.VITE_API_URL}/logistics/upload/`,
        form
      );
      const { redis_key, redis_key_pdf } = up.data;

      // 2) Kick off check‐delta
      const kick = await axios.post(
        `${import.meta.env.VITE_API_URL}/logistics/check-delta/`,
        { partner, redis_key, redis_key_pdf, delta_threshold: 20 }
      );
      setTaskId(kick.data.task_id);
      setPolling(true);
    } catch (e) {
      setError(e.response?.data?.error || e.message);
    }
  };

  // Polling effect
  useEffect(() => {
    if (!polling || !taskId) return;

    pollRef.current = setInterval(async () => {
      try {
        const status = await axios.get(
          `${import.meta.env.VITE_API_URL}/logistics/task-status/`,
          { params: { task_id: taskId } }
        );
        if (status.data.state === "SUCCESS") {
          clearInterval(pollRef.current);
          setPolling(false);

          // 4) fetch the result
          const result = await axios.get(
            `${import.meta.env.VITE_API_URL}/logistics/task-result/`,
            { params: { task_id: taskId } }
          );
          const { delta_ok, parsed_ok, delta_sum, data, sheet_url } = result.data;

          setDeltaOk(delta_ok && parsed_ok);
          setDeltaSum(delta_sum);
          setSheetUrl(sheet_url);
          setData(data);
        }
        else if (status.data.state === "FAILURE") {
          clearInterval(pollRef.current);
          setPolling(false);
          setError("Processing failed on server.");
        }
      } catch (err) {
        clearInterval(pollRef.current);
        setPolling(false);
        setError("Error polling task status.");
      }
    }, 2000); // every 2s

    return () => clearInterval(pollRef.current);
  }, [polling, taskId]);

  return (
    <div className="ml-64 p-8 space-y-8">
      <h1 className="text-4xl font-bold">Invoice Dashboard</h1>
      <div className="flex space-x-2">
        {partnerOptions.map((p) => (
          <button
            key={p}
            onClick={() => setPartner(p)}
            className={`px-4 py-2 rounded-lg border ${
              partner === p
                ? "bg-indigo-600 text-white"
                : "bg-white text-gray-700"
            }`}
          >
            {p.replace(/_/g, " ").toUpperCase()}
          </button>
        ))}
      </div>

      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        className="border-2 border-dashed rounded-xl h-56 flex flex-col items-center justify-center hover:bg-gray-100"
      >
        <UploadCloud className="h-12 w-12 text-gray-400" />
        <p>Drag & drop .pdf/.xls/.xlsx here</p>
        <input
          type="file"
          multiple
          accept=".pdf,.xls,.xlsx"
          onChange={handleChange}
          className="absolute inset-0 opacity-0 cursor-pointer"
        />
      </div>

      <button
        onClick={startProcess}
        disabled={polling || !files}
        className="px-6 py-3 bg-indigo-600 text-white rounded-lg disabled:opacity-50"
      >
        {polling ? "Processing…" : "Upload & Analyze"}
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
              <a href={sheetUrl} target="_blank" rel="noopener" className="text-indigo-600">
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
