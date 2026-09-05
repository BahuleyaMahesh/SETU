import React from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { AppLogo } from '../../shared/components/AppLogo';
import { ThemeToggle } from '../../shared/components/ThemeToggle';
import { useAuth } from '../auth/AuthProvider';
import { Home, ClipboardList, Bell, MessageSquare, User, LogOut, Pill } from 'lucide-react';

interface PatientLayoutProps {
  children?: React.ReactNode;
}

export const PatientLayout: React.FC<PatientLayoutProps> = ({ children }) => {
  const location = useLocation();
  const { logout, user } = useAuth();
  const activeTab = location.pathname.split('/')[2] || 'home';

  const navItems = [
    { id: 'home', path: '/patient/home', label: 'Home', icon: Home },
    { id: 'checkup', path: '/patient/checkup', label: 'Checkup', icon: ClipboardList },
    { id: 'reminders', path: '/patient/reminders', label: 'Reminders', icon: Bell },
    { id: 'prescriptions', path: '/patient/prescriptions', label: 'Meds', icon: Pill },
    { id: 'chat', path: '/patient/chat', label: 'Assistant', icon: MessageSquare },
    { id: 'profile', path: '/patient/profile', label: 'Profile', icon: User },
  ];

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col font-sans antialiased transition-colors">
      {/* Top Header */}
      <header className="sticky top-0 z-30 bg-white/90 dark:bg-slate-900/90 backdrop-blur border-b border-slate-200 dark:border-slate-800 px-4 py-3 shadow-sm transition-colors">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <AppLogo size="sm" />
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-slate-600 dark:text-slate-400 hidden sm:inline-block">
              {user?.full_name || 'Patient Portal'}
            </span>
            <ThemeToggle />
            <button
              onClick={logout}
              className="p-1.5 text-slate-500 dark:text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-slate-800 rounded-lg transition-colors"
              title="Sign Out"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-4xl w-full mx-auto p-4 sm:p-6 pb-28">
        {children || <Outlet />}
      </main>

      {/* Bottom Mobile & Tablet Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 z-40 bg-white/95 dark:bg-slate-900/95 backdrop-blur border-t border-slate-200 dark:border-slate-800 px-2 py-2 shadow-lg transition-colors">
        <div className="flex justify-around items-center max-w-lg mx-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <Link
                key={item.id}
                to={item.path}
                className={`flex flex-col items-center gap-1 py-1 px-3 rounded-xl transition-all duration-200 ${
                  isActive
                    ? 'text-sky-600 bg-sky-50 dark:bg-sky-950 dark:text-sky-400 font-semibold'
                    : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100/60 dark:hover:bg-slate-800/60'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="text-[11px]">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
};

export default PatientLayout;
