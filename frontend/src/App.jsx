//frontend/src/App.jsx
import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import Analytics from "./pages/Analytics";
import Slack from "./pages/Slack";

export default function App() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <Router>
      <div className="flex">
        <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
        <main
          className={`flex-1 transition-all duration-300 ${
            collapsed ? "ml-16" : "ml-64"
          } bg-gray-50 min-h-screen p-8`}
        >
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/slack" element={<Slack />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}
