import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import { useAuth } from '../hooks/useAuth';

export default function Layout() {
  const { user } = useAuth();

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-700">HydroMind Ecosystem</h2>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-500">
              {user?.display_name} ({user?.role})
            </span>
            <div className="w-8 h-8 rounded-full bg-hydro-500 text-white flex items-center justify-center text-sm font-medium">
              {user?.username?.[0]?.toUpperCase() || 'U'}
            </div>
          </div>
        </header>

        {/* Main content */}
        <main className="flex-1 p-6 overflow-auto bg-gray-50">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
