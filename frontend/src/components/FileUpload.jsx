//frontend/src/components/FileUpload.jsx
import React, { useState } from "react";
import axios from "axios";

const FileUpload = ({ partner, setPartner, onUpload }) => {
  const [files, setFiles] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const form = new FormData();
    files.forEach((file) => form.append("file", file));
    form.append("partner_value", partner);
    await axios.post("/upload", form);
    onUpload();
  };

  return (
    <form onSubmit={handleSubmit} className="mb-6 space-y-4">
      <select
        value={partner}
        onChange={(e) => setPartner(e.target.value)}
        className="border p-2"
      >
        <option value="brenger">Brenger</option>
        <option value="wuunder">Wuunder</option>
        <option value="libero_logistics">Libero</option>
        <option value="swdevries">Swdevries</option>
        <option value="transpoksi">Transpoksi</option>
        <option value="magic_movers">Magic Movers</option>
      </select>

      <input
        type="file"
        multiple
        accept=".pdf,.xlsx,.csv"
        onChange={(e) => setFiles(Array.from(e.target.files))}
        className="block"
      />

      <button type="submit" className="px-4 py-2 bg-black text-white rounded">
        Upload
      </button>
    </form>
  );
};

export default FileUpload;
