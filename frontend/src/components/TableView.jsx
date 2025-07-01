//frontend/src/components/TableView.jsx
import React from "react";

const TableView = ({ data }) => {
  if (!data || !data.length) return null;

  const columns = Object.keys(data[0]);

  return (
    <div className="overflow-x-auto shadow border rounded mb-6">
      <table className="min-w-full text-sm text-left">
        <thead>
          <tr className="bg-gray-200">
            {columns.map((col) => (
              <th key={col} className="px-4 py-2 font-medium">{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, idx) => (
            <tr key={idx} className={row.Delta >= 0 ? "bg-green-100" : ""}>
              {columns.map((col) => (
                <td key={col} className="px-4 py-2">{row[col]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TableView;
