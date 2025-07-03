//frontend/src/components/Sidebar.jsx
// src/components/Sidebar.jsx
import { useState } from "react";
import { LayoutDashboard, BarChart, MessageSquare, Menu } from "lucide-react";
import { Link, useLocation } from "react-router-dom";

const navItems = [
  { name: "Dashboard", path: "/", icon: LayoutDashboard },
  { name: "Analytics", path: "/analytics", icon: BarChart },
  { name: "Slack", path: "/slack", icon: MessageSquare },
];

export default function Sidebar({ collapsed, setCollapsed }) {
  const location = useLocation();

  return (
    <div
      className={`h-screen bg-gray-900 text-white flex flex-col transition-all duration-300 ${
        collapsed ? "w-16" : "w-64"
      }`}
    >
      <div className="flex items-center justify-between p-4">
        <button onClick={() => setCollapsed(!collapsed)}>
          <Menu className="text-white" />
        </button>
        {!collapsed && <h1 className="text-lg font-bold">LogiDash</h1>}
      </div>

      <nav className="flex-1">
        <ul className="space-y-2 px-2">
          {navItems.map(({ name, path, icon: Icon }) => (
            <li key={name}>
              <Link
                to={path}
                className={`flex items-center gap-4 p-2 rounded-lg transition hover:bg-gray-800 ${
                  location.pathname === path ? "bg-gray-800" : ""
                }`}
              >
                <Icon size={20} />
                {!collapsed && <span>{name}</span>}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}
