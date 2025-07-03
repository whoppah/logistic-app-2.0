// src/pages/Slack.jsx
import { useEffect, useState, useRef } from 'react';
import axios from 'axios';

export default function Slack() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(true);
  const listRef = useRef(null);

  // Fetch recent Slack messages from backend
  const fetchMessages = async () => {
    try {
      const res = await axios.get(`${import.meta.env.VITE_API_URL}/slack/messages`);
      setMessages(res.data);
    } catch (err) {
      console.error('Error fetching Slack messages', err);
    } finally {
      setLoading(false);
      scrollToBottom();
    }
  };

  // Send a new Slack message via backend
  const handleSend = async () => {
    if (!input.trim()) return;
    try {
      const res = await axios.post(`${import.meta.env.VITE_API_URL}/slack/send`, {
        text: input
      });
      setInput('');
      setMessages((prev) => [...prev, res.data]);
      scrollToBottom();
    } catch (err) {
      console.error('Error sending Slack message', err);
    }
  };

  const scrollToBottom = () => {
    setTimeout(() => {
      listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' });
    }, 100);
  };

  useEffect(() => {
    fetchMessages();
    const interval = setInterval(fetchMessages, 5000); // auto-refresh
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col h-full max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold pb-4 border-b">Slack Channel</h1>

      {loading ? (
        <div className="flex-1 flex items-center justify-center">Loading messages…</div>
      ) : (
        <div
          ref={listRef}
          className="flex-1 overflow-auto space-y-4 p-4 bg-white rounded-lg shadow"
        >
          {messages.map((msg) => (
            <div key={msg.ts} className="flex space-x-3">
              <img
                src={msg.user_avatar}
                alt={msg.user_name}
                className="w-10 h-10 rounded-full"
              />
              <div>
                <p className="text-sm font-semibold">{msg.user_name}</p>
                <p className="text-gray-700">{msg.text}</p>
                <p className="text-xs text-gray-400">{new Date(msg.ts * 1000).toLocaleString()}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-4 flex space-x-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Type a message..."
          className="flex-1 border px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={handleSend}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
        >
          Send
        </button>
      </div>
    </div>
  );
}
