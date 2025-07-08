// frontend/src/pages/Slack.jsx
import React, { useEffect, useState } from "react";
import axios from "axios";
import ChannelHeader from "../components/ChannelHeader";
import MessageList from "../components/MessageList";
import ThreadSidebar from "../components/ThreadSidebar";

export default function Slack() {
  const API = import.meta.env.VITE_API_URL;
  const [messages, setMessages] = useState([]);
  const [selectedThreadTs, setThreadTs] = useState(null);
  const [threads, setThreads] = useState({});
  const [loading, setLoading] = useState(true);

  // fetch top‐level messages
  useEffect(() => {
    (async () => {
      try {
        const res = await axios.get(`${API}/logistics/slack/messages/`);
        setMessages(res.data);
      } finally {
        setLoading(false);
      }
    })();
  }, [API]);

  // open a thread
  const openThread = async (ts) => {
    setThreadTs(ts);
    if (!threads[ts]) {
      const res = await axios.get(`${API}/logistics/slack/threads/`, {
        params: { thread_ts: ts },
      });
      setThreads((t) => ({ ...t, [ts]: res.data }));
    }
  };

  // add or remove a reaction
  const handleReact = async (ts, reaction) => {
    await axios.post(`${API}/logistics/slack/react/`, { ts, reaction });
    // immediately refresh just that one message's data:
    setMessages((msgs) =>
      msgs.map((m) =>
        m.ts === ts
          ? {
              ...m,
              // bump the count locally so UI updates instantly:
              reactions: m.reactions.map((r) =>
                r.name === reaction
                  ? { ...r, count: r.count + 1 }
                  : r
              ),
            }
          : m
      )
    );
  };

  return (
    <div className="flex h-screen">
      {/* main column */}
      <div
        className={`flex flex-col ${
          selectedThreadTs ? "w-2/3 border-r" : "w-full"
        }`}
      >
        <ChannelHeader name="invoices-logistics" />

        <div className="flex-1 overflow-auto bg-white">
          {loading ? (
            <div className="p-4 text-center text-gray-500">Loading…</div>
          ) : (
            <MessageList
              messages={messages}
              onOpenThread={openThread}
              onReact={handleReact}
              selectedThreadTs={selectedThreadTs}
            />
          )}
        </div>

        <div className="p-3 border-t bg-gray-50">
          <input
            placeholder="Message #invoices-logistics"
            className="w-full px-4 py-2 rounded-full border focus:outline-none focus:ring"
            disabled
          />
        </div>
      </div>

      {/* sidebar */}
      {selectedThreadTs && (
        <ThreadSidebar
          threadTs={selectedThreadTs}
          messages={threads[selectedThreadTs] || []}
          onClose={() => setThreadTs(null)}
        />
      )}
    </div>
  );
}
