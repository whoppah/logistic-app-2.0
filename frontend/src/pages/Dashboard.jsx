//frontend/src/pages/Dashboard.jsx
import { useState } from "react";
import { UploadCloud, Loader2, FileBarChart2, CheckCircle2, AlertTriangle } from "lucide-react";

export default function Dashboard() {
  const [uploading, setUploading] = useState(false);
  const [data, setData] = useState(null);
  const [partner, setPartner] = useState("brenger");
  const [error, setError] = useState("");

  const handleFileUpload = async (event) => {
    const files = event.target.files;
    if (!files.length) return;

    setUploading(true);
    setError("");
    setData(null);

    const formData = new FormData();
    Array.from(files).forEach((file) => formData.append("file", file));
    formData.append("partner_value", partner);

    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/upload`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error("Upload failed");
      const result = await res.json();
      setData(result);
    } catch (err) {
      console.error(err);
      setError("Failed to process the file.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="mb-4">
        <h1 className="text-3xl font-bold">Logistics Dashboard</h1>
        <p className="text-gray-600">Upload invoice files and get delta insights</p>
      </div>

      {/* File Upload */}
      <div className="bg-white rounded-xl p-6 shadow space-y-4">
        <label className="block text-sm font-medium mb-2">Select Partner</label>
        <select
          value={partner}
          onChange={(e) => setPartner(e.target.value)}
          className="border rounded px-3 py-2 w-full"
        >
          <option value="brenger">Brenger</option>
          <option value="sendy">Sendy</option>
        </select>

        <label className="block text-sm font-medium mt-4 mb-2">Upload Invoice Files</label>
        <div className="border-2 border-dashed rounded p-6 text-center cursor-pointer">
          <input type="file" multiple onChange={handleFileUpload} className="hidden" id="file-upload" />
          <label htmlFor="file-upload" className="cursor-pointer">
            <UploadCloud className="mx-auto mb-2 w-8 h-8 text-gray-500" />
            <p className="text-gray-700">Drag and drop or click to upload</p>
          </label>
        </div>
      </div>

      {/* Loading / Error */}
      {uploading && (
        <div className="flex items-center space-x-2 text-blue-600">
          <Loader2 className="animate-spin" />
          <span>Processing...</span>
        </div>
      )}
      {error && (
        <div className="flex items-center space-x-2 text-red-600">
          <AlertTriangle />
          <span>{error}</span>
        </div>
      )}

      {/* Result Card */}
      {data && (
        <div className="bg-white p-6 rounded-xl shadow space-y-2">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold">Delta Summary</h2>
              <p className="text-gray-500 text-sm">Partner: {partner}</p>
            </div>
            <CheckCircle2 className="text-green-500 w-6 h-6" />
          </div>
          <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gray-50 p-4 rounded border">
              <p className="text-sm text-gray-600">Delta Sum</p>
              <p className="text-2xl font-bold">{data.delta_sum}</p>
            </div>
            <div className="bg-gray-50 p-4 rounded border">
              <p className="text-sm text-gray-600">Deltas OK</p>
              <p className="text-2xl font-bold">{data.delta_ok ? "Yes" : "No"}</p>
            </div>
          </div>
          {data.message && (
            <div className="mt-4 text-sm text-gray-700">{data.message}</div>
          )}
        </div>
      )}

      {/* Table */}
      {data?.data && (
        <div className="bg-white p-6 rounded-xl shadow">
          <h3 className="text-lg font-medium mb-4">Invoice Delta Table</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full border text-sm">
              <thead>
                <tr className="bg-gray-100">
                  {Object.keys(data.data[0]).map((key) => (
                    <th key={key} className="px-3 py-2 text-left font-semibold border-b">
                      {key}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.data.map((row, idx) => (
                  <tr key={idx} className="border-b hover:bg-gray-50">
                    {Object.values(row).map((val, i) => (
                      <td key={i} className="px-3 py-2">
                        {val}
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
