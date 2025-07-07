// frontend/src/pages/Slack.jsx
import { useEffect, useState, useRef } from "react";
import axios from "axios";

export default function Slack() {
  const API_BASE = import.meta.env.VITE_API_URL || "";
  const [messages, setMessages]       = useState([]);
  const [threadMessages, setThread]   = useState({});
  const [loadingMsgs, setLoadingMsgs] = useState(true);
  const [loadingThread, setLoadingThread] = useState(null);
  const listRef = useRef(null);

  // Scroll to bottom when messages or a thread loads
  const scrollToBottom = () => {
    setTimeout(() => {
      listRef.current?.scrollTo({
        top: listRef.current.scrollHeight,
        behavior: "smooth",
      });
    }, 100);
  };

  // Fetch top-level messages on mount
  useEffect(() => {
    async function fetchMessages() {
      try {
        const res = await axios.get(`${API_BASE}/slack/messages/`);
        setMessages(res.data);
      } catch (err) {
        console.error("Error fetching Slack messages", err);
      } finally {
        setLoadingMsgs(false);
        scrollToBottom();
      }
    }
    fetchMessages();
  }, [API_BASE]);

  // Fetch a thread when its badge is clicked
  const handleShowThread = async (threadTs) => {
    if (threadMessages[threadTs]) {
      // already loaded → toggle visibility
      setThread(prev => {
        const copy = { ...prev };
        delete copy[threadTs];
        return copy;
      });
      return;
    }

    setLoadingThread(threadTs);
    try {
      const res = await axios.get(`${API_BASE}/slack/threads/`, {
        params: { thread_ts: threadTs },
      });
      setThread(prev => ({ ...prev, [threadTs]: res.data }));
    } catch (err) {
      console.error("Error fetching thread", err);
    } finally {
      setLoadingThread(null);
      scrollToBottom();
    }
  };

  return (
    <div className="flex flex-col h-full max-w-2xl mx-auto p-4">
      <h1 className="text-3xl font-bold pb-4 border-b">Slack Channel</h1>

      {loadingMsgs ? (
        <div className="flex-1 flex items-center justify-center">Loading messages…</div>
      ) : (
        <div
          ref={listRef}
          className="flex-1 overflow-auto space-y-4 p-4 bg-white rounded-lg shadow"
        >
          {messages.map((msg) => {
            const { ts, user_name, text, reply_count } = msg;
            const thread = threadMessages[ts] || [];
            return (
              <div key={ts} className="space-y-2">
                {/* Top-level message */}
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-sm font-semibold">{user_name}</p>
                    <p className="text-gray-700">{text}</p>
                    <p className="text-xs text-gray-400">
                      {new Date(parseFloat(ts) * 1000).toLocaleString()}
                    </p>
                  </div>
                  {reply_count > 0 && (
                    <button
                      onClick={() => handleShowThread(ts)}
                      className="text-xs bg-gray-100 px-2 py-1 rounded-full hover:bg-gray-200"
                      disabled={loadingThread === ts}
                    >
                      {loadingThread === ts
                        ? "Loading…"
                        : `${reply_count} repl${reply_count > 1 ? "ies" : "y"}`}
                    </button>
                  )}
                </div>

                {/* Thread messages */}
                {thread.length > 0 && (
                  <div className="ml-6 border-l-2 border-gray-200 pl-4 space-y-2">
                    {thread.map((t) => (
                      <div key={t.ts}>
                        <p className="text-sm font-medium">{t.user_name}</p>
                        <p className="text-gray-700">{t.text}</p>
                        <p className="text-xs text-gray-400">
                          {new Date(parseFloat(t.ts) * 1000).toLocaleString()}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Input bar */}
      <div className="mt-4 flex space-x-2">
        <input
          type="text"
          placeholder="Type a message..."
          className="flex-1 border px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled
        />
        <button
          className="px-4 py-2 bg-green-600 text-white rounded-lg opacity-50 cursor-not-allowed"
          disabled
        >
          Send
        </button>
      </div>
    </div>
  );
}
