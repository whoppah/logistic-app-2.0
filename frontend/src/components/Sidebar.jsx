//frontend/src/components/Sidebar.jsx
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Upload,
  BarChart2,
  MessageCircle,
} from 'lucide-react';

const navItems = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Upload', path: '/upload', icon: Upload },
  { name: 'Analytics', path: '/analytics', icon: BarChart2 },
  { name: 'Slack Config', path: '/slack', icon: MessageCircle },
];

export default function Sidebar() {
  const { pathname } = useLocation();

  return (
    <aside className="w-64 h-screen bg-white border-r shadow-sm fixed top-0 left-0 flex flex-col z-50">
      <div className="text-2xl font-semibold px-6 py-4 border-b">
        Facturen Logistiek
      </div>
      <nav className="flex flex-col gap-1 p-4">
        {navItems.map(({ name, path, icon: Icon }) => (
          <Link
            key={path}
            to={path}
            className={`flex items-center gap-3 px-4 py-2 rounded-lg text-sm transition-all font-medium ${
              pathname === path
                ? 'bg-blue-100 text-blue-700'
                : 'hover:bg-gray-100 text-gray-700'
            }`}
          >
            <Icon size={18} />
            {name}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
