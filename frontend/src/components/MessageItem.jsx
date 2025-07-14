//frontend/src/components/MessageItem.jsx
import React from "react";
import { useNavigate } from "react-router-dom";
import {
  UserCircle2,
  MessageSquare,
  FileText,
  FileSpreadsheet,
} from "lucide-react";

// Map free‐form Slack message text to partner key and desired file type
const PARTNER_MAP = [
  { label: /brenger/i,         key: "brenger",      want: "pdf"  },
  { label: /libero/i,          key: "libero",       want: "both" },
  { label: /sw\s*de\s*vries/i, key: "swdevries",    want: "xls"  },
  { label: /transpoksi/i,      key: "transpoksi",   want: "pdf"  },
  { label: /wuunder/i,         key: "wuunder",      want: "pdf"  },
  { label: /magic\s*movers/i,  key: "magic_movers", want: "xls"  },
  { label: /tadde/i,           key: "tadde",        want: "both" },
];

export default function MessageItem({
  msg,
  isSelected,
  onOpenThread,
  onOptimisticReact,
  onSendReact,
}) {
  const navigate = useNavigate();
  const time = new Date(parseFloat(msg.ts) * 1000).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  const handleReact = (name) => {
    onOptimisticReact(msg.ts, name);
    onSendReact(msg.ts, name);
  };

  // 1️⃣ Detect partner from the message text
  const match = PARTNER_MAP.find(({ label }) => label.test(msg.text));
  const partner = match?.key;

  // 2️⃣ Collect all matching file URLs for that partner
  let fileUrls = [];
  if (partner) {
    const want = match.want;
    for (let f of msg.files || []) {
      if (
        (want === "pdf"  && f.mimetype === "application/pdf") ||
        (want === "xls"  && f.mimetype.includes("spreadsheet")) ||
        (want === "both" && (f.mimetype === "application/pdf" || f.mimetype.includes("spreadsheet")))
      ) {
        fileUrls.push(f.url);
      }
    }
  }

  // 3️⃣ Clicking Analyze navigates to Dashboard with state
  const handleAnalyze = () => {
    if (!partner || fileUrls.length === 0) return;
    navigate("/", { state: { partner, fileUrls } });
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

          {/* ➕ Analyze button ➕ */}
          {partner && fileUrls.length > 0 && (
            <button
              onClick={handleAnalyze}
              className="ml-4 px-2 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700"
            >
              Analyze
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
