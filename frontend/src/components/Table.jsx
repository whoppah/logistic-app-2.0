//frontend/src/components/Table.jsx
import React from "react";
import PropTypes from "prop-types";

export default function Table({ data, columns }) {
  if (!Array.isArray(data) || data.length === 0) {
    return <p className="text-gray-500">No data to display</p>;
  }
  const cols = columns
    ? columns
    : Object.keys(data[0]).map((key) => ({ key, label: key }));

  return (
    <div className="overflow-x-auto">
      <table className="table-auto w-full border-collapse">
        <thead>
          <tr>
            {cols.map(({ key, label }) => (
              <th
                key={key}
                className="px-4 py-2 bg-gray-100 text-left text-xs font-semibold text-gray-700 uppercase"
              >
                {label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, idx) => (
            <tr
              key={idx}
              className={idx % 2 === 0 ? "bg-white" : "bg-gray-50"}
            >
              {cols.map(({ key }) => (
                <td key={key} className="px-4 py-2 text-sm text-gray-800">
                  {typeof row[key] === "number"
                    ? row[key].toFixed(2)
                    : row[key]?.toString() ?? ""}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

Table.propTypes = {
  data: PropTypes.arrayOf(PropTypes.object).isRequired,
  columns: PropTypes.arrayOf(
    PropTypes.shape({
      key: PropTypes.string.isRequired,
      label: PropTypes.string,
    })
  ),
};

Table.defaultProps = {
  columns: null,
};
