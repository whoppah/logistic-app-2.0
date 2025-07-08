// frontend/src/components/MessageList.jsx
import React from "react";
import MessageItem from "./MessageItem";

export default function MessageList({
  messages,
  onOpenThread,
  onReact,
  selectedThreadTs,
}) {
  // group by calendar date
  const byDate = messages.reduce((acc, m) => {
    const date = new Date(parseFloat(m.ts) * 1000).toLocaleDateString();
    acc[date] = acc[date] || [];
    acc[date].push(m);
    return acc;
  }, {});

  return (
    <div className="p-4 space-y-6">
      {Object.entries(byDate).map(([date, msgs]) => (
        <div key={date}>
          {/* date separator */}
          <div className="text-center text-xs text-gray-400 mb-4">
            {date}
          </div>

          <div className="space-y-4">
            {msgs
              .sort((a, b) => parseFloat(a.ts) - parseFloat(b.ts)) // oldest → newest
              .map((msg) => (
                <MessageItem
                  key={msg.ts}
                  msg={msg}
                  isSelected={msg.ts === selectedThreadTs}
                  onOpenThread={() => onOpenThread(msg.ts)}
                  onReact={onReact}
                />
              ))}
          </div>
        </div>
      ))}
    </div>
  );
}
