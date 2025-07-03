// src/pages/SlackSettings.jsx
import React, { useState } from "react";
import axios from "axios";

const SlackSettings = () => {
  const [connected, setConnected] = useState(false);

  const connectSlack = async () => {
    const res = await axios.get("/logistics/slack/oauth-url");
    window.location.href = res.data.url;
  };

  return (
    <div>
      <h2 className="text-xl mb-4">Slack Integration</h2>
      {connected ? (
        <div className="text-green-600">Connected</div>
      ) : (
        <button onClick={connectSlack} className="bg-black text-white px-4 py-2 rounded">
          Connect to Slack
        </button>
      )}
    </div>
  );
};

export default SlackSettings;
