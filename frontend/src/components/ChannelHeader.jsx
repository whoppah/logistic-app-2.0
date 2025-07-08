// frontend/src/components/ChannelHeader.jsx
import React from "react";
import { HashStraight as Hashtag } from "lucide-react";

export default function ChannelHeader({ name }) {
  return (
    <div className="flex items-center p-4 border-b bg-gray-100">
      <Hashtag className="mr-2 text-gray-500" />
      <h2 className="font-semibold text-gray-800">{name}</h2>
      {/* you can add search, info icons here */}
    </div>
  );
}
