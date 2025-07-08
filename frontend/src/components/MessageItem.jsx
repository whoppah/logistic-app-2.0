// frontend/src/components/MessageItem.jsx
import React from "react";
import axios from "axios";
import {
  UserCircle2,
  MessageSquare,
  FileText,
  FileSpreadsheet,
} from "lucide-react";

export default function MessageItem({ msg, isSelected, onOpenThread }) {
  const time = new Date(parseFloat(msg.ts) * 1000)
    .toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  const toggleReaction = async (name) => {
    await axios.post(
      `${import.meta.env.VITE_API_URL}/logistics/slack/react/`,
      { ts: msg.ts, reaction: name }
    );
    onReact(msg.ts, name);
  };

  return (
    <div
      className={`relative group flex space-x-3 p-2 ${
        isSelected ? "bg-gray-800 bg-opacity-10 rounded-lg" : ""
      }`}
    >
      {/* ─── 1) hover toolbar ─────────────────────────────────────────────── */}
      <div
        className="
          absolute top-1 right-2
          opacity-0 group-hover:opacity-100 transition-opacity duration-150
          z-20
        "
      >
        <div
          className="
            flex space-x-1 
            bg-gray-900 bg-opacity-90 
            px-2 py-1 rounded-md 
            shadow-lg
            text-white text-sm
          "
        >
          <button
            onClick={() => toggleReaction("white_check_mark")}
            className="flex items-center justify-center w-6 h-6 rounded hover:bg-white hover:bg-opacity-20"
          >
            ✅
          </button>
          <button
            onClick={() => toggleReaction("large_red_square")}
            className="flex items-center justify-center w-6 h-6 rounded hover:bg-white hover:bg-opacity-20"
          >
            🟥
          </button>
        </div>
      </div>

      {/* ─── 2) avatar + body ────────────────────────────────────────────── */}
      <UserCircle2 className="w-8 h-8 text-gray-400" />
      <div className="flex-1">
        <div className="flex items-baseline space-x-2">
          <span className="text-sm font-medium text-gray-200">
            {msg.user_name}
          </span>
          <span className="text-xs text-gray-500">{time}</span>
        </div>
        <p className="mt-1 text-gray-300">{msg.text}</p>

        {/* attachments, reactions, reply‐count… */}
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
                  className="
                    inline-flex items-center space-x-1 
                    border border-gray-700 
                    rounded px-2 py-1 
                    bg-gray-800 hover:bg-gray-700
                  "
                >
                  {isPdf ? (
                    <FileText className="w-4 h-4 text-red-400" />
                  ) : isXlsx ? (
                    <FileSpreadsheet className="w-4 h-4 text-green-400" />
                  ) : (
                    <FileText className="w-4 h-4 text-gray-400" />
                  )}
                  <span className="text-xs text-gray-200 truncate max-w-[100px]">
                    {f.name}
                  </span>
                </a>
              );
            })}
          </div>
        )}

        {msg.reactions?.length > 0 && (
          <div className="mt-2 flex space-x-1">
            {msg.reactions.map((r) => (
              <button
                key={r.name}
                onClick={() => toggleReaction(r.name)}
                className="
                  inline-flex items-center 
                  bg-gray-800 hover:bg-gray-700 
                  rounded px-2 py-1 text-xs text-gray-200
                "
              >
                <span className="mr-1">
                  {r.name === "white_check_mark" ? "✅" : "🟥"}
                </span>
                <span>{r.count}</span>
              </button>
            ))}
          </div>
        )}

        {msg.reply_count > 0 && (
          <button
            onClick={onOpenThread}
            className="mt-2 flex items-center space-x-1 text-xs text-blue-400 hover:underline"
          >
            <MessageSquare className="w-4 h-4" />
            <span>
              {msg.reply_count} repl{msg.reply_count > 1 ? "ies" : "y"}
            </span>
          </button>
        )}
      </div>
    </div>
  );
}
