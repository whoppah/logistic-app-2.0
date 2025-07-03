// src/components/Layout.jsx
import React from "react";
import Sidebar from "./Sidebar";

const Layout = ({ children }) => (
  <div className="flex min-h-screen bg-gray-50 text-gray-800">
    <Sidebar />
    <main className="flex-1 p-6 overflow-auto">{children}</main>
  </div>
);

export default Layout;
