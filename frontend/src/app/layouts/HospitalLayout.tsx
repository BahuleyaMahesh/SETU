import React from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { AppLogo } from '../../shared/components/AppLogo';
import { ThemeToggle } from '../../shared/components/ThemeToggle';
import { useAuth } from '../auth/AuthProvider';
import { LayoutDashboard, Users, Bell, BarChart3, FileText, MapPin, LogOut } from 'lucide-react';

interface HospitalLayoutProps {
  children?: React.ReactNode;
}

export const HospitalLayout: React.FC<HospitalLayoutProps> = ({ children }) => {
  const location = useLocation();
  const { logout, user } = useAuth();
  const activeTab = location.pathname.split('/')[2] || 'dashboard';

  const navItems = [
    { id: 'dashboard', path: '/hospital/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'patients', path: '/hospital/patients', label: 'Patients', icon: Users },
    { id: 'alerts', path: '/hospital/alerts', label: 'Alert Queue', icon: Bell, hasBadge: true },
    { id: 'analytics', path: '/hospital/analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'reports', path: '/hospital/reports', label: 'Reports', icon: FileText },
    { id: 'map', path: '/hospital/map', label: 'Hospital Map', icon: MapPin },
  ];

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex font-sans antialiased transition-colors">
      {/* Sidebar Desktop */}
      <aside className="w-64 bg-slate-900 text-slate-200 hidden md:flex flex-col fixed inset-y-0 z-40 border-r border-slate-800">
        <div className="p-6 border-b border-slate-800">
          <AppLogo size="md" className="text-white" />
          <div className="mt-2 text-xs font-medium text-slate-400">
            Hospital Clinical Desk
          </div>
        </div>

        <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <Link
                key={item.id}
                to={item.path}
                className={`flex items-center gap-3.5 px-4 py-3 rounded-xl transition-all duration-200 font-medium text-sm ${
                  isActive
                    ? 'bg-sky-600 text-white shadow-lg shadow-sky-600/20'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                }`}
              >
                <div className="relative">
                  <Icon className="w-5 h-5" />
                  {item.hasBadge && (
                    <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-red-500 rounded-full ring-2 ring-slate-900" />
                  )}
                </div>
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-slate-800">
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
          >
            <LogOut className="w-5 h-5" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 md:ml-64 flex flex-col min-h-screen">
        <header className="bg-white/90 dark:bg-slate-900/90 backdrop-blur border-b border-slate-200 dark:border-slate-800 px-6 py-4 flex justify-between items-center sticky top-0 z-30 shadow-sm transition-colors">
          <div className="flex items-center gap-3">
            <div className="md:hidden">
              <AppLogo size="sm" />
            </div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 capitalize tracking-tight hidden sm:block">
              {activeTab} Overview
            </h2>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-sm font-semibold text-slate-800 dark:text-slate-100">{user?.full_name || 'Hospital Admin'}</div>
              <div className="text-xs text-slate-500 dark:text-slate-400">{user?.role?.toUpperCase() || 'HOSPITAL'}</div>
            </div>
            <ThemeToggle />
            <button
              onClick={logout}
              className="p-2 text-slate-500 dark:text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-slate-800 rounded-xl transition-colors md:hidden"
              title="Sign Out"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </header>

        <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
          {children || <Outlet />}
        </main>
      </div>
    </div>
  );
};

export default HospitalLayout;
