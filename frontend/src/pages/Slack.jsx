//frontend/src/pages/Slack.jsx
import { useEffect, useState } from "react";
import axios from "axios";
import MessageList from "../components/MessageList";
import ThreadSidebar from "../components/ThreadSidebar";

export default function Slack() {
  const API_BASE = import.meta.env.VITE_API_URL || "";
  const [messages, setMessages]     = useState([]);
  const [selectedThreadTs, setThreadTs] = useState(null);
  const [threads, setThreads]       = useState({});  

  // fetch top-level messages on mount...
  useEffect(() => { /* ... */ }, [API_BASE]);

  const openThread = async (threadTs) => {
    setThreadTs(threadTs);
    if (!threads[threadTs]) {
      const res = await axios.get(`${API_BASE}/logistics/slack/threads/`, {
        params: { thread_ts: threadTs },
      });
      setThreads(t => ({ ...t, [threadTs]: res.data }));
    }
  };

  return (
    <div className="flex h-full">
      {/* Left pane: message list */}
      <div className="w-2/3 border-r overflow-auto">
        <MessageList
          messages={messages}
          onOpenThread={openThread}
          selectedThreadTs={selectedThreadTs}
        />
      </div>

      {/* Right pane: thread sidebar */}
      {selectedThreadTs && (
        <div className="w-1/3 bg-gray-50 overflow-auto">
          <ThreadSidebar
            threadTs={selectedThreadTs}
            messages={threads[selectedThreadTs] || []}
            onClose={() => setThreadTs(null)}
          />
        </div>
      )}
    </div>
  );
}
