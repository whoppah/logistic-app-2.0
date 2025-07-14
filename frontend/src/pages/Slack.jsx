// frontend/src/pages/Slack.jsx
import React, { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import ChannelHeader from "../components/ChannelHeader";
import MessageList from "../components/MessageList";
import ThreadSidebar from "../components/ThreadSidebar";

export default function Slack() {
  const API = import.meta.env.VITE_API_URL;
  const navigate = useNavigate();

  const [messages, setMessages]         = useState([]);
  const [selectedThreadTs, setThreadTs] = useState(null);
  const [threads, setThreads]           = useState({});
  const [loading, setLoading]           = useState(true);

  //Load channel messages once on mount
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

  //Open a thread and fetch its replies if needed
  const openThread = async (ts) => {
    setThreadTs(ts);
    if (!threads[ts]) {
      try {
        const res = await axios.get(`${API}/logistics/slack/threads/`, {
          params: { thread_ts: ts },
        });
        setThreads((t) => ({ ...t, [ts]: res.data.filter((m) => m && m.ts) }));
      } catch (e) {
        console.error("Error fetching Slack thread", e);
      }
    }
  };

  //Reactions
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
        if (!found) newReactions.push({ name, count: 1, me: true });
        return { ...m, reactions: newReactions };
      })
    );
  };
  const sendReact = async (ts, reaction) => {
    try {
      await axios.post(`${API}/logistics/slack/react/`, { ts, reaction });
    } catch (e) {
      console.error("Error sending reaction", e);
    }
  };

  // etch thread attachments & navigate to Dashboard
  const fetchThreadAndAnalyze = async (threadTs, partner) => {
    // ensure we have the thread loaded
    let thread = threads[threadTs];
    if (!thread) {
      const res = await axios.get(`${API}/logistics/slack/threads/`, {
        params: { thread_ts: threadTs },
      });
      thread = res.data;
      setThreads((t) => ({ ...t, [threadTs]: thread }));
    }

    // define mimetypes we want per partner
    const WANT = {
      brenger:      ["application/pdf"],
      libero:       ["application/pdf","spreadsheet"],
      swdevries:    ["spreadsheet"],
      transpoksi:   ["application/pdf"],
      wuunder:      ["application/pdf"],
      magic_movers: ["spreadsheet"],
      tadde:        ["application/pdf","spreadsheet"],
    }[partner] || [];

    // collect all file URLs from any message in the thread
    const urls = thread
      .flatMap((m) => m.files || [])
      .filter((f) => WANT.some((w) => f.mimetype.includes(w)))
      .map((f) => f.url);

    if (urls.length === 0) {
      alert("No matching invoice files found in this thread.");
      return;
    }

    // navigate to the Dashboard, passing state
    navigate("/", { state: { partner, fileUrls: urls } });
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
              onOptimisticReact={optimisticReact}
              onSendReact={sendReact}
              fetchThreadAndAnalyze={fetchThreadAndAnalyze}  // ← pass it down
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
