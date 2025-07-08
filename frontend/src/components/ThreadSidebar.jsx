// frontend/src/components/ThreadSidebar.jsx
import React from "react";
import { X, UserCircle2 } from "lucide-react";

export default function ThreadSidebar({ threadTs, messages, onClose }) {
  const headerTime = new Date(parseFloat(threadTs) * 1000)
    .toLocaleString();

  return (
    <div className="w-1/3 flex flex-col border-l bg-gray-50">
      <div className="flex items-center justify-between p-4 border-b">
        <div>
          <span className="font-semibold">Thread</span>
          <div className="text-xs text-gray-500">{headerTime}</div>
        </div>
        <button onClick={onClose}>
          <X className="w-5 h-5 text-gray-500 hover:text-gray-700" />
        </button>
      </div>

      <div className="flex-1 overflow-auto p-4 space-y-4">
        {messages.map(m => {
          const time = new Date(parseFloat(m.ts) * 1000).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});
          return (
            <div key={m.ts} className="flex space-x-3">
              <UserCircle2 className="w-8 h-8 text-gray-400" />
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium">{m.user_name}</span>
                  <span className="text-xs text-gray-400">{time}</span>
                </div>
                <p className="mt-1 text-gray-700">{m.text}</p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="p-4 border-t">
        <input
          placeholder="Reply in thread"
          className="w-full px-4 py-2 rounded-full border focus:outline-none focus:ring"
          disabled
        />
      </div>
    </div>
  );
}
