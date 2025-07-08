// frontend/src/components/MessageItem.jsx
import React from "react";
import axios from "axios";
import {
  UserCircle2,
  MessageSquare,
  FileText,
  FileSpreadsheet,
  Check,
  Square,
} from "lucide-react";

export default function MessageItem({
  msg,
  isSelected,
  onOpenThread,
}) {
  const time = new Date(parseFloat(msg.ts) * 1000)
    .toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  // send a reaction via backend
  const handleReact = async (reactionName) => {
    try {
      await axios.post(
        `${import.meta.env.VITE_API_URL}/logistics/slack/react/`,
        { ts: msg.ts, reaction: reactionName }
      );
    } catch (e) {
      console.error("React error", e);
    }
  };

  return (
    <div
      className={`flex space-x-3 p-2 ${isSelected ? "bg-gray-100 rounded-lg" : ""}`}
    >
      <UserCircle2 className="w-8 h-8 text-gray-400" />

      <div className="flex-1">
        {/* header */}
        <div className="flex items-baseline space-x-2">
          <span className="text-sm font-medium text-gray-800">
            {msg.user_name}
          </span>
          <span className="text-xs text-gray-400">{time}</span>
        </div>

        {/* text */}
        <p className="mt-1 text-gray-700">{msg.text}</p>

        {/* attachments */}
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

        {/* replies & reactions */}
        <div className="mt-3 flex items-center space-x-4 text-gray-500">
          {/* reply count */}
          {msg.reply_count > 0 && (
            <button
              onClick={onOpenThread}
              className="flex items-center space-x-1 text-xs hover:text-gray-700"
            >
              <MessageSquare className="w-4 h-4" />
              <span>
                {msg.reply_count} repl
                {msg.reply_count > 1 ? "ies" : "y"}
              </span>
            </button>
          )}

          {/* reactions */}
          <button
            onClick={() => handleReact("white_check_mark")}
            className="p-1 hover:bg-gray-200 rounded-full"
          >
            <Check className="w-4 h-4 text-green-500" />
          </button>
          <button
            onClick={() => handleReact("large_red_square")}
            className="p-1 hover:bg-gray-200 rounded-full"
          >
            <Square className="w-4 h-4 text-red-500" />
          </button>
        </div>
      </div>
    </div>
  );
}
