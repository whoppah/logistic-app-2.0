//frontend/src/components/Sidebar.jsx
import {
  MenuIcon,
  HomeIcon,
  BarChart2Icon,
  MessageCircleIcon,
} from "lucide-react";
import { Link, useLocation } from "react-router-dom";

const navItems = [
  { to: "/", label: "Dashboard", icon: <HomeIcon /> },
  { to: "/analytics", label: "Analytics", icon: <BarChart2Icon /> },
  { to: "/slack", label: "Slack", icon: <MessageCircleIcon /> },
];

export default function Sidebar({ collapsed, setCollapsed }) {
  const { pathname } = useLocation();

  return (
    <div
      className={`fixed top-0 left-0 h-full bg-white border-r 
        flex flex-col transition-width duration-300
        ${collapsed ? "w-16" : "w-64"}`}
    >
      {/* Profile */}
      <div className="flex items-center justify-between p-4">
        {!collapsed && (
          <div className="flex items-center space-x-3">
            <img
              src="/whoppah_logo.png"
              alt="Whoppah"
              className="w-8 h-8 rounded-full"
            />
            <span className="font-semibold">Logistics 2.0</span>
          </div>
        )}
        <button onClick={() => setCollapsed(!collapsed)}>
          <MenuIcon className="h-6 w-6 text-gray-600" />
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 mt-4">
        {navItems.map(item => {
          const active = pathname === item.to;
          return (
            <Link
              key={item.to}
              to={item.to}
              className={`
                flex items-center gap-3 px-4 py-3 mx-2 my-1 rounded-lg
                transition-colors duration-150
                ${active
                  ? "bg-indigo-50 text-indigo-600 border-l-4 border-indigo-600"
                  : "text-gray-600 hover:bg-gray-100"}
              `}
              title={collapsed ? item.label : undefined}
            >
              <div className="h-5 w-5">{item.icon}</div>
              {!collapsed && <span className="font-medium">{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div className="p-4 text-xs text-gray-400">
          Whoppah
        </div>
      )}
    </div>
  );
}
