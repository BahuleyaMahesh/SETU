import React from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { AppLogo } from '../../shared/components/AppLogo';
import { ThemeToggle } from '../../shared/components/ThemeToggle';
import { useAuth } from '../auth/AuthProvider';
import { Home, Users, Bell, MapPin, LogOut } from 'lucide-react';

interface AshaLayoutProps {
  children?: React.ReactNode;
}

export const AshaLayout: React.FC<AshaLayoutProps> = ({ children }) => {
  const location = useLocation();
  const { logout, user } = useAuth();
  const activeTab = location.pathname.split('/')[2] || 'home';

  const navItems = [
    { id: 'home', path: '/asha/home', label: 'Home', icon: Home },
    { id: 'patients', path: '/asha/patients', label: 'Patients', icon: Users },
    { id: 'alerts', path: '/asha/alerts', label: 'Alerts', icon: Bell, hasBadge: true },
    { id: 'map', path: '/asha/map', label: 'Field Map', icon: MapPin },
  ];

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col font-sans antialiased transition-colors">
      {/* Top Header */}
      <header className="sticky top-0 z-30 bg-white/90 dark:bg-slate-900/90 backdrop-blur border-b border-slate-200 dark:border-slate-800 px-4 py-3 shadow-sm transition-colors">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AppLogo size="sm" />
            <span className="hidden sm:inline-block px-2.5 py-0.5 rounded-full bg-teal-50 dark:bg-teal-950 border border-teal-200 dark:border-teal-800 text-teal-700 dark:text-teal-400 text-xs font-semibold">
              ASHA Worker Portal
            </span>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <div className="text-sm font-semibold text-slate-800 dark:text-slate-100">{user?.full_name || 'ASHA Worker'}</div>
              <div className="text-xs text-slate-500 dark:text-slate-400">Field Monitoring</div>
            </div>
            <ThemeToggle />
            <button
              onClick={logout}
              className="p-2 text-slate-500 dark:text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-slate-800 rounded-xl transition-colors"
              title="Sign Out"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-6xl w-full mx-auto p-4 sm:p-6 pb-28">
        {children || <Outlet />}
      </main>

      {/* Bottom Navigation for Mobile */}
      <nav className="fixed bottom-0 left-0 right-0 z-40 bg-white/95 dark:bg-slate-900/95 backdrop-blur border-t border-slate-200 dark:border-slate-800 px-2 py-2 shadow-lg transition-colors">
        <div className="flex justify-around items-center max-w-md mx-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <Link
                key={item.id}
                to={item.path}
                className={`flex flex-col items-center gap-1 py-1 px-4 rounded-xl transition-all duration-200 relative ${
                  isActive
                    ? 'text-teal-700 bg-teal-50 dark:bg-teal-950 dark:text-teal-400 font-semibold'
                    : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100/60 dark:hover:bg-slate-800/60'
                }`}
              >
                <div className="relative">
                  <Icon className="w-5 h-5" />
                  {item.hasBadge && (
                    <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-red-500 rounded-full ring-2 ring-white" />
                  )}
                </div>
                <span className="text-[11px]">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
};

export default AshaLayout;
