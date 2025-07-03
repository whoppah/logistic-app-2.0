//frontend/src/components/Sidebar.jsx
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Upload,
  BarChart2,
  MessageCircle,
} from 'lucide-react';

const navItems = [
  { name: 'Dashboard', path: '/', icon: <LayoutDashboard size={18} /> },
  { name: 'Upload', path: '/upload', icon: <Upload size={18} /> },
  { name: 'Analytics', path: '/analytics', icon: <BarChart2 size={18} /> },
  { name: 'Slack', path: '/slack', icon: <MessageCircle size={18} /> },
];

export default function Sidebar() {
  const { pathname } = useLocation();

  return (
    <aside className="w-64 h-screen bg-white border-r shadow-sm fixed top-0 left-0 flex flex-col">
      <div className="text-xl font-bold p-4 border-b">Facturen Logistiek</div>
      <nav className="flex flex-col p-4 gap-2">
        {navItems.map(({ name, path, icon }) => (
          <Link
            key={path}
            to={path}
            className={`flex items-center gap-3 px-3 py-2 rounded-md transition-colors ${
              pathname === path
                ? 'bg-blue-100 text-blue-700 font-medium'
                : 'hover:bg-gray-100 text-gray-700'
            }`}
          >
            {icon}
            <span>{name}</span>
          </Link>
        ))}
      </nav>
    </aside>
  );
}
