//frontend/src/components/Sidebar.jsx
import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Menu,
  LayoutDashboard,
  Upload,
  BarChart2,
  MessageCircle,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

const navItems = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Upload', path: '/upload', icon: Upload },
  { name: 'Analytics', path: '/analytics', icon: BarChart2 },
  { name: 'Slack Config', path: '/slack', icon: MessageCircle },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const { pathname } = useLocation();

  return (
    <aside
      className={`h-screen bg-white border-r shadow-sm fixed top-0 left-0 flex flex-col transition-all duration-300 z-50 ${
        collapsed ? 'w-16' : 'w-64'
      }`}
    >
      <div className="flex items-center justify-between px-4 py-4 border-b">
        {!collapsed && <span className="text-lg font-semibold">Logistiek</span>}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="text-gray-600 hover:text-black"
        >
          {collapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
        </button>
      </div>

      <nav className="flex flex-col gap-1 px-2 py-4">
        {navItems.map(({ name, path, icon: Icon }) => (
          <Link
            key={path}
            to={path}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-all text-sm font-medium ${
              pathname === path
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            <Icon size={18} />
            {!collapsed && <span>{name}</span>}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
