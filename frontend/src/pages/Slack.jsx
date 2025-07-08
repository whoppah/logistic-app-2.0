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

  // 1️⃣ Load channel messages once on mount
  useEffect(() => {
    (async () => {
      try {
        const res = await axios.get(`${API}/logistics/slack/messages/`);
        setMessages(res.data.filter((m) => m && m.ts));
      } catch (e) {
        console.error("Error fetching Slack messages", e);
      } finally {
        setLoading(false);
      }
    })();
  }, [API]);

  // 2️⃣ Open a thread and fetch its replies if needed
  const openThread = async (ts) => {
    setThreadTs(ts);
    if (!threads[ts]) {
      try {
        const res = await axios.get(`${API}/logistics/slack/threads/`, {
          params: { thread_ts: ts },
        });
        setThreads((t) => ({
          ...t,
          [ts]: res.data.filter((m) => m && m.ts),
        }));
      } catch (e) {
        console.error("Error fetching Slack thread", e);
      }
    }
  };

  // 3️⃣ Optimistic local reaction update
  const optimisticReact = (ts, name) => {
    setMessages((msgs) =>
      msgs.map((m) => {
        if (m.ts !== ts) return m;
        let found = false;
        const newReactions = (m.reactions || []).map((r) => {
          if (r.name === name) {
            found = true;
            return { ...r, count: r.count + 1, me: true };
          }
          return r;
        });
        if (!found) {
          newReactions.push({ name, count: 1, me: true });
        }
        return { ...m, reactions: newReactions };
      })
    );
  };

  // 4️⃣ Fire off to backend/slack — errors can be ignored here, UI already updated
  const sendReact = async (ts, reaction) => {
    try {
      await axios.post(`${API}/logistics/slack/react/`, { ts, reaction });
    } catch (e) {
      console.error("Error sending reaction", e);
    }
  };

  return (
    <div className="flex h-screen">
      {/* Main column */}
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
              // pass both helpers down
              onOptimisticReact={optimisticReact}
              onSendReact={sendReact}
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
