// frontend/src/components/ThreadSidebar.jsx
export default function ThreadSidebar({ threadTs, messages, onClose }) {
  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <h2 className="font-bold">Thread</h2>
        <button onClick={onClose} className="text-xl">&times;</button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {messages.map((m) => (
          <div key={m.ts} className="space-y-1">
            <p className="font-semibold">{m.user_name}</p>
            <p>{m.text}</p>
            <p className="text-xs text-gray-400">
              {new Date(parseFloat(m.ts) * 1000).toLocaleString()}
            </p>
          </div>
        ))}
      </div>

      {/* Reply input placeholder */}
      <div className="p-4 border-t">
        <input
          type="text"
          placeholder="Reply in thread…"
          className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring"
          disabled
        />
      </div>
    </div>
  );
}
