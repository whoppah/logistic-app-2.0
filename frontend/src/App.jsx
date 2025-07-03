//frontend/src/App.jsx
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import Analytics from './pages/Analytics';
import Slack from './pages/Slack';

export default function App() {
  return (
    <Router>
      <div className="flex">
        <Sidebar />
        <main className="ml-64 w-full min-h-screen bg-gray-50 p-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/slack" element={<Slack />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}
