import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../../app/theme/ThemeProvider';

interface ThemeToggleProps {
  className?: string;
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({ className = '' }) => {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
      aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
      className={`p-2 rounded-xl text-slate-500 hover:text-sky-600 hover:bg-sky-50 dark:text-slate-400 dark:hover:text-sky-400 dark:hover:bg-slate-800 transition-colors ${className}`}
    >
      {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
    </button>
  );
};

export default ThemeToggle;
