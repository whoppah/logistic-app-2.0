//frontend/src/components/Sidebar.jsx
import React from "react";
import {
  MenuIcon,
  GridIcon,
  BarChart2Icon,
  SlackIcon,
} from "lucide-react";
import { Link, useLocation } from "react-router-dom";

const navItems = [
  { label: "Dashboard", to: "/", icon: <GridIcon /> },
  { label: "Analytics", to: "/analytics", icon: <BarChart2Icon /> },
  { label: "Slack", to: "/slack", icon: <SlackIcon /> },
];

export default function Sidebar({ collapsed, setCollapsed }) {
  const { pathname } = useLocation();

  return (
    <div
      className={`
        fixed top-0 left-0 h-full bg-white border-r border-gray-200
        transition-width duration-300 flex flex-col
        ${collapsed ? "w-16" : "w-64"}
      `}
    >
      {/* collapse/expand toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="p-3 hover:bg-gray-100 focus:outline-none"
      >
        <MenuIcon className="h-5 w-5 text-gray-700" />
      </button>

      {/* logo or title */}
      {!collapsed && (
        <div className="px-4 py-2 text-xl font-bold text-gray-800">
          Logistics 2.0
        </div>
      )}

      {/* nav links */}
      <nav className="mt-4 flex-1">
        {navItems.map(({ label, to, icon }) => {
          const isActive = pathname === to;
          return (
            <Link
              key={to}
              to={to}
              className={`
                flex items-center gap-3 px-4 py-3 mx-2 my-1 rounded-lg
                ${isActive
                  ? "bg-indigo-50 text-indigo-600"
                  : "text-gray-600 hover:bg-gray-100"}
              `}
            >
              <div className="h-5 w-5">{icon}</div>
              {!collapsed && (
                <span className="font-medium">{label}</span>
              )}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
