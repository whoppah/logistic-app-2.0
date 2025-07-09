// frontend/src/components/ThreadSidebar.jsx
import React from "react";
import axios from "axios";
import { X, FileText, FileSpreadsheet } from "lucide-react";

export default function ThreadSidebar({
  threadTs,
  messages = [],
  onClose,
  onOptimisticReact,
  onSendReact,
}) {
  const headerTime = new Date(parseFloat(threadTs) * 1000).toLocaleString();

  const handleReact = (ts, name) => {
    onOptimisticReact(ts, name);
    onSendReact(ts, name);
  };

  return (
    <div className="w-1/3 flex flex-col border-l bg-gray-50">
      {/* header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div>
          <span className="font-semibold">Thread</span>
          <div className="text-xs text-gray-500">{headerTime}</div>
        </div>
        <button onClick={onClose}>
          <X className="w-5 h-5 text-gray-500 hover:text-gray-700" />
        </button>
      </div>

      {/* messages */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {messages.map((m) => {
          const time = new Date(parseFloat(m.ts) * 1000)
            .toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

          return (
            <div key={m.ts} className="flex space-x-3">
              {/* avatar */}
              {m.user_avatar ? (
                <img
                  src={m.user_avatar}
                  alt={m.user_name}
                  className="w-8 h-8 rounded-full flex-shrink-0"
                />
              ) : (
                <div className="w-8 h-8 bg-gray-300 rounded-full" />
              )}

              <div className="flex-1">
                {/* author/time */}
                <div className="flex items-baseline space-x-2">
                  <span className="text-sm font-medium text-gray-800">
                    {m.user_name}
                  </span>
                  <span className="text-xs text-gray-400">{time}</span>
                </div>

                {/* text */}
                <p className="mt-1 text-gray-700">{m.text}</p>

                {/* attachments */}
                {m.files?.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {m.files.map((f) => {
                      const isPdf = f.mimetype === "application/pdf";
                      const isXlsx = f.mimetype.includes("spreadsheet");
                      return (
                        <a
                          key={f.id}
                          href={f.url}
                          target="_blank"
                          rel="noopener"
                          className="inline-flex items-center space-x-1 border rounded px-2 py-1 bg-gray-100 hover:bg-gray-200"
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

                {/* reactions */}
                {m.reactions?.length > 0 && (
                  <div className="mt-2 flex space-x-1">
                    {m.reactions.map((r) => (
                      <button
                        key={r.name}
                        onClick={() => handleReact(m.ts, r.name)}
                        className="inline-flex items-center bg-gray-200 hover:bg-gray-300 rounded px-2 py-1 text-xs"
                      >
                        <span className="mr-1">
                          {r.name === "white_check_mark" ? "✅" : "🟥"}
                        </span>
                        <span>{r.count}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* reply box */}
      <div className="p-4 border-t bg-white">
        <input
          placeholder="Reply in thread…"
          className="w-full px-4 py-2 rounded-full border focus:outline-none focus:ring"
          disabled
        />
      </div>
    </div>
  );
}
