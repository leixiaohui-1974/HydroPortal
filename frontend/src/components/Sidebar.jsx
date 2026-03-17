import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const NAV_ITEMS = [
  { to: '/', label: '总览', icon: '📊', roles: ['admin', 'designer', 'operator'] },
  { to: '/guard', label: 'HydroGuard', icon: '🛡️', roles: ['admin', 'operator'] },
  { to: '/design', label: 'HydroDesign', icon: '📐', roles: ['admin', 'designer'] },
  { to: '/lab', label: 'HydroLab', icon: '🔬', roles: ['admin', 'designer'] },
  { to: '/edu', label: 'HydroEdu', icon: '📚', roles: ['admin', 'designer', 'operator'] },
  { to: '/arena', label: 'HydroArena', icon: '🏆', roles: ['admin'] },
  { to: '/settings', label: '设置', icon: '⚙️', roles: ['admin', 'designer', 'operator'] },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const role = user?.role || '';

  const visibleItems = NAV_ITEMS.filter((item) => item.roles.includes(role));

  return (
    <aside className="w-60 bg-hydro-900 text-white flex flex-col min-h-screen">
      {/* Logo / Brand */}
      <div className="px-6 py-5 border-b border-hydro-700">
        <h1 className="text-xl font-bold tracking-wide">HydroPortal</h1>
        <p className="text-xs text-hydro-300 mt-1">水网门户</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4">
        {visibleItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-6 py-3 text-sm transition-colors ${
                isActive
                  ? 'bg-hydro-700 text-white font-medium'
                  : 'text-hydro-200 hover:bg-hydro-800 hover:text-white'
              }`
            }
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* User info + logout */}
      <div className="px-6 py-4 border-t border-hydro-700">
        <p className="text-sm font-medium">{user?.display_name}</p>
        <p className="text-xs text-hydro-400">{role}</p>
        <button
          onClick={logout}
          className="mt-3 text-xs text-hydro-300 hover:text-white transition-colors"
        >
          退出登录
        </button>
      </div>
    </aside>
  );
}
