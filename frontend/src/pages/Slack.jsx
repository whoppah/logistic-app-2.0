// frontend/src/pages/Slack.jsx
import React, { useEffect, useState } from "react";
import axios from "axios";
import ChannelHeader from "../components/ChannelHeader";
import MessageList from "../components/MessageList";
import ThreadSidebar from "../components/ThreadSidebar";

export default function Slack() {
  const API = import.meta.env.VITE_API_URL;
  const [messages, setMessages]         = useState([]);
  const [selectedThreadTs, setThreadTs] = useState(null);
  const [threads, setThreads]           = useState({});
  const [loading, setLoading]           = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await axios.get(`${API}/logistics/slack/messages/`);
        setMessages(res.data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    })();
  }, [API]);

  const openThread = async (ts) => {
    setThreadTs(ts);
    if (!threads[ts]) {
      const res = await axios.get(`${API}/logistics/slack/threads/`, {
        params: { thread_ts: ts },
      });
      setThreads(t => ({ ...t, [ts]: res.data }));
    }
  };

  return (
    <div className="flex h-screen">
      {/* Main column */}
      <div className="flex flex-col w-2/3 border-r">
        <ChannelHeader name="invoices-logistics" />

        <div className="flex-1 overflow-auto bg-white">
          {loading ? (
            <div className="p-4 text-center text-gray-500">Loading…</div>
          ) : (
            <MessageList
              messages={messages}
              onOpenThread={openThread}
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

      {/* Thread sidebar */}
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
