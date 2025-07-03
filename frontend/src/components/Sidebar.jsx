//frontend/src/components/Sidebar.jsx
import React from "react";
import { Link } from "react-router-dom";

const Sidebar = () => (
  <div className="w-64 bg-white border-r shadow-sm">
    <div className="p-4 text-xl font-bold">Facturen Logistiek</div>
    <ul className="space-y-2 px-4 mt-4 text-gray-700">
      <li><Link to="/launch" className="hover:text-black">Dashboard</Link></li>
      <li><Link to="/" className="hover:text-black">Upload</Link></li>
      <li><Link to="/analytics" className="hover:text-black">Analytics</Link></li>
      <li><Link to="/slack" className="hover:text-black">Slack</Link></li>
    </ul>
  </div>
);

export default Sidebar;
