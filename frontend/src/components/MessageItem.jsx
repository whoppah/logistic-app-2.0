//frontend/src/components/MessageItem.jsx
import React from "react";
import { useNavigate } from "react-router-dom";
import {
  UserCircle2,
  MessageSquare,
  FileText,
  FileSpreadsheet,
} from "lucide-react";

const PARTNER_MAP = [
  { label: /\bbrenger\b/i,         key: "brenger",      want: "pdf"  },
  { label: /\blibero\b/i,          key: "libero",       want: "both" },
  { label: /\bsw\s+de\s+vries\b/i, key: "swdevries",    want: "xls"  },
  { label: /\btranspoksi\b/i,      key: "transpoksi",   want: "pdf"  },
  { label: /\bwuunder\b/i,         key: "wuunder",      want: "pdf"  },
  { label: /\bmagic\s+movers\b/i,  key: "magic_movers", want: "xls"  },
  { label: /\btadde\b/i,           key: "tadde",        want: "both" },
];

export default function MessageItem(props) {
  const { msg, isSelected, onOpenThread, onOptimisticReact, onSendReact } = props;
  const navigate = useNavigate();

  // DEBUG: what text are we actually getting?
  console.log("🔍 Slack text:", msg.text);

  // Regex lookup
  let match = PARTNER_MAP.find(({ label }) => label.test(msg.text));

  // Fallback: simple substring if regex failed
  if (!match) {
    const lower = msg.text.toLowerCase();
    if (lower.includes("brenger"))      match = PARTNER_MAP.find(m => m.key==="brenger");
    else if (lower.includes("libero"))  match = PARTNER_MAP.find(m => m.key==="libero");
    else if (lower.includes("sw de vries")) match = PARTNER_MAP.find(m => m.key==="swdevries");
    else if (lower.includes("wuunder")) match = PARTNER_MAP.find(m => m.key==="wuunder");
    // …and so on for other partners…
  }

  const partner = match?.key;
  console.log("   → detected partner:", partner);

  //  Collect file URLs (same as before)…
  let fileUrls = [];
  if (partner) {
    const want = match.want;
    for (let f of msg.files || []) {
      if (
        (want==="pdf"  && f.mimetype==="application/pdf") ||
        (want==="xls"  && f.mimetype.includes("spreadsheet")) ||
        (want==="both" && (f.mimetype==="application/pdf" || f.mimetype.includes("spreadsheet")))
      ) {
        fileUrls.push(f.url);
      }
    }
  }
  console.log("   → matching files:", fileUrls);

  // Clicking Analyze navigates to Dashboard with state
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
