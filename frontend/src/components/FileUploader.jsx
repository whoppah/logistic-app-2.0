//frontend/src/components/FileUploader.jsx
import { UploadCloud } from "lucide-react";

export default function FileUploader({ onFiles, files }) {
  return (
    <div
      onDrop={e => { e.preventDefault(); onFiles(e.dataTransfer.files); }}
      onDragOver={e => e.preventDefault()}
      className={`
        relative w-full max-w-lg mx-auto p-8
        border-2 rounded-xl bg-white shadow hover:shadow-md
        transition-shadow duration-200
        ${files?.length ? "border-green-400" : "border-gray-200"}
      `}
    >
      <div className="flex flex-col items-center justify-center text-gray-500 space-y-4">
        <UploadCloud className="h-12 w-12" />
        <h3 className="text-lg font-semibold">Drag & Drop Files</h3>
        <p className="text-sm">Or click to browse your computer</p>
      </div>
      <input
        type="file"
        multiple
        accept=".pdf,.xls,.xlsx"
        onChange={e => onFiles(e.target.files)}
        className="absolute inset-0 opacity-0 cursor-pointer"
      />

      {files?.length > 0 && (
        <div className="mt-6 space-y-2">
          <h4 className="font-medium">Selected files:</h4>
          <ul className="list-disc list-inside text-sm text-gray-700">
            {files.map((f, i) => (
              <li key={i} className="flex justify-between">
                <span className="truncate max-w-xs">{f.name}</span>
                <button
                  onClick={() => onFiles(files.filter((_, idx) => idx !== i))}
                  className="text-red-500 hover:text-red-700"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
