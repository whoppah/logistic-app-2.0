// frontend/src/components/MessageItem.jsx
import React from "react";
import { UserCircle2, MessageSquare } from "lucide-react";

export default function MessageItem({ msg, isSelected, onOpenThread }) {
  const time = new Date(parseFloat(msg.ts) * 1000).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

  return (
    <div className={`flex space-x-3 ${isSelected ? "bg-gray-100 rounded-lg p-2" : ""}`}>
      <UserCircle2 className="w-8 h-8 text-gray-400" />
      <div className="flex-1">
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-gray-800">{msg.user_name}</span>
          <span className="text-xs text-gray-400">{time}</span>
        </div>
        <p className="mt-1 text-gray-700">{msg.text}</p>

        {/* attachments */}
        {msg.files?.length > 0 && (
          <div className="mt-2 space-y-2">
            {msg.files.map(f => (
              <a
                key={f.id}
                href={f.url}
                target="_blank"
                rel="noopener"
                className="inline-flex items-center space-x-2 border rounded px-3 py-1 bg-gray-50 hover:bg-gray-100"
              >
                <MessageSquare className="w-4 h-4 text-gray-500" />
                <span className="text-xs text-gray-700 truncate max-w-xs">
                  {f.name}
                </span>
              </a>
            ))}
          </div>
        )}

        {/* reply count */}
        {msg.reply_count > 0 && (
          <button
            onClick={onOpenThread}
            className="mt-2 inline-flex items-center text-xs text-gray-500 hover:text-gray-700"
          >
            <MessageSquare className="w-4 h-4 mr-1" />
            {msg.reply_count} repl{msg.reply_count > 1 ? "ies" : "y"}
          </button>
        )}
      </div>
    </div>
  );
}
