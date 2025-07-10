// frontend/src/components/Sidebar.jsx
import React, { useState, useEffect } from "react";
import {
  MenuIcon,
  HomeIcon,
  BarChart2Icon,
  MessageCircleIcon,
  TagIcon,
} from "lucide-react";
import { Link, useLocation } from "react-router-dom";

const navItems = [
  { to: "/",          label: "Dashboard", icon: <HomeIcon /> },
  { to: "/analytics", label: "Analytics", icon: <BarChart2Icon /> },
  { to: "/slack",     label: "Slack",     icon: <MessageCircleIcon /> },
  { to: "/pricing",   label: "Pricing",   icon: <TagIcon /> },
];

export default function Sidebar({ collapsed, setCollapsed }) {
  const { pathname } = useLocation();

  return (
    <div
      className={`
        fixed top-0 left-0 h-full bg-white border-r
        flex flex-col
        transition-all duration-300 ease-in-out
        ${collapsed ? "w-16" : "w-64"}
      `}
    >
      {/* Profile / Brand */}
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
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 rounded hover:bg-gray-100"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <MenuIcon className="h-6 w-6 text-gray-600" />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 mt-4">
        {navItems.map((item) => {
          const active = pathname === item.to;
          return (
            <Link
              key={item.to}
              to={item.to}
              title={collapsed ? item.label : undefined}
              className={`
                flex items-center gap-3
                px-4 py-3 mx-2 my-1 rounded-lg
                transition-colors duration-150
                ${active
                  ? "bg-accent/10 text-accent border-l-4 border-accent"
                  : "text-gray-600 hover:bg-gray-100"}
              `}
            >
              <div className="h-5 w-5 flex-shrink-0">
                {React.cloneElement(item.icon, {
                  className: active ? "text-accent" : "text-gray-600",
                  size: 20,
                })}
              </div>
              {!collapsed && <span className="font-medium">{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div className="p-4 text-xs text-gray-400">
          &copy; Whoppah
        </div>
      )}
    </div>
  );
}
