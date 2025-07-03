//frontend/src/App.jsx
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useState } from 'react';

import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import Slack from './pages/Slack';

export default function App() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <Router>
      <div className="flex">
        {/* Sidebar with collapsed state control */}
        <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />

        {/* Main content shifts based on sidebar width */}
        <main
          className={`transition-all duration-300 min-h-screen bg-gray-50 p-6 ${
            collapsed ? 'ml-16' : 'ml-64'
          }`}
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
