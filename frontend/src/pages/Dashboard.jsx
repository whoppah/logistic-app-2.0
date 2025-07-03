//frontend/src/pages/Dashboard.jsx
import { useState } from "react";
import { CloudUpload } from "lucide-react";

export default function Dashboard() {
  const [partner, setPartner] = useState("brenger");
  const [files, setFiles] = useState(null);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Logistics Dashboard</h1>
        <p className="text-gray-600">Upload invoice files and get delta insights</p>
      </div>

      <div className="bg-white p-6 rounded-xl shadow space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-4">
            <label htmlFor="partner" className="font-semibold">
              Select Partner
            </label>
            <select
              id="partner"
              value={partner}
              onChange={(e) => setPartner(e.target.value)}
              className="border rounded px-3 py-2"
            >
              <option value="brenger">Brenger</option>
              <option value="postnl">PostNL</option>
              <option value="dhl">DHL</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label
              htmlFor="file-upload"
              className="cursor-pointer inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              <CloudUpload className="mr-2" size={18} />
              Upload Invoice Files
            </label>
            <input
              id="file-upload"
              type="file"
              className="hidden"
              onChange={(e) => setFiles(e.target.files)}
              multiple
            />
          </div>
        </div>

        <div className="border-2 border-dashed rounded-lg p-8 text-center text-gray-500 hover:bg-gray-50 transition">
          Drag and drop or click to upload
        </div>
      </div>
    </div>
  );
}
