// frontend/src/components/MessageItem.jsx
import React from "react";
import {
  UserCircle2,
  MessageSquare,
  FileText,
  FileSpreadsheet,
} from "lucide-react";

export default function MessageItem({
  msg,
  isSelected,
  onOpenThread,
  onOptimisticReact,
  onSendReact,
}) {
  const time = new Date(parseFloat(msg.ts) * 1000).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  const handleReact = (name) => {
    onOptimisticReact(msg.ts, name);
    onSendReact(msg.ts, name);
  };

  return (
    <div
      className={`relative group flex space-x-3 p-3 ${
        isSelected ? "bg-gray-100 rounded-lg" : "hover:bg-gray-50"
      }`}
    >
      <UserCircle2 className="w-8 h-8 text-gray-400 flex-shrink-0" />

      <div className="flex-1">
        <div className="flex items-baseline space-x-2">
          <span className="text-sm font-medium text-gray-800">
            {msg.user_name}
          </span>
          <span className="text-xs text-gray-400">{time}</span>
        </div>

        <p className="mt-1 text-gray-700">{msg.text}</p>

        {msg.files?.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {msg.files.map((f) => {
              const isPdf = f.mimetype === "application/pdf";
              const isXlsx = f.mimetype.includes("spreadsheet");
              return (
                <a
                  key={f.id}
                  href={f.url}
                  target="_blank"
                  rel="noopener"
                  className="inline-flex items-center space-x-1 border rounded px-2 py-1 bg-gray-50 hover:bg-gray-100"
                >
                  {isPdf ? (
                    <FileText className="w-4 h-4 text-red-500" />
                  ) : isXlsx ? (
                    <FileSpreadsheet className="w-4 h-4 text-green-500" />
                  ) : (
                    <FileText className="w-4 h-4 text-gray-500" />
                  )}
                  <span className="text-xs text-gray-700 truncate max-w-[100px]">
                    {f.name}
                  </span>
                </a>
              );
            })}
          </div>
        )}

        <div className="mt-2 flex items-center space-x-2">
          {msg.reactions?.map((r) => (
            <button
              key={r.name}
              onClick={() => handleReact(r.name)}
              className="inline-flex items-center bg-gray-200 hover:bg-gray-300 rounded px-2 py-1 text-xs"
            >
              <span className="mr-1">
                {r.name === "white_check_mark" ? "✅" : "🟥"}
              </span>
              <span>{r.count}</span>
            </button>
          ))}

          {msg.reply_count > 0 && (
            <button
              onClick={onOpenThread}
              className="flex items-center space-x-1 text-xs text-blue-600 hover:underline"
            >
              <MessageSquare className="w-4 h-4" />
              <span>
                {msg.reply_count} repl{msg.reply_count > 1 ? "ies" : "y"}
              </span>
            </button>
          )}
        </div>
      </div>

      {/* hover picker */}
      <div className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={() => handleReact("white_check_mark")}
          className="p-1 bg-white rounded hover:bg-gray-200"
        >
          ✅
        </button>
        <button
          onClick={() => handleReact("large_red_square")}
          className="ml-1 p-1 bg-white rounded hover:bg-gray-200"
        >
          🟥
        </button>
      </div>
    </div>
  );
}
