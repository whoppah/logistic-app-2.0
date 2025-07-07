// frontend/src/components/MessageList.jsx
export default function MessageList({ messages, onOpenThread, selectedThreadTs }) {
  return (
    <div className="space-y-4 p-4">
      {messages.map((m) => (
        <div
          key={m.ts}
          className={`p-3 rounded-lg hover:bg-gray-100 ${
            selectedThreadTs === m.ts ? "bg-gray-200" : ""
          }`}
        >
          <div className="flex justify-between">
            <div>
              <p className="font-semibold">{m.user_name}</p>
              <p>{m.text}</p>
              <p className="text-xs text-gray-400">
                {new Date(parseFloat(m.ts) * 1000).toLocaleString()}
              </p>
            </div>
            {m.reply_count > 0 && (
              <button
                onClick={() => onOpenThread(m.ts)}
                className="text-xs bg-gray-200 px-2 py-1 rounded-full"
              >
                {m.reply_count} repl{m.reply_count > 1 ? "ies" : "y"}
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
