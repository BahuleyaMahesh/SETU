import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../app/auth/AuthProvider';

interface AppLogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
}

export const AppLogo: React.FC<AppLogoProps> = ({
  className = '',
  size = 'md',
  showText = true,
}) => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const handleLogoClick = () => {
    if (!user) {
      navigate('/');
    } else if (user.role === 'patient') {
      navigate('/patient/checkup');
    } else if (user.role === 'asha') {
      navigate('/asha/home');
    } else if (user.role === 'hospital' || user.role === 'admin') {
      navigate('/hospital/dashboard');
    } else {
      navigate('/');
    }
  };

  const heights = {
    sm: 'h-8',
    md: 'h-10',
    lg: 'h-14',
  };

  return (
    <div
      onClick={handleLogoClick}
      className={`inline-flex items-center gap-3 cursor-pointer select-none group ${className || 'text-slate-800 dark:text-slate-100'}`}
    >
      <img
        src="/setu-logo.svg"
        alt="SETU Healthcare"
        className={`${heights[size]} w-auto object-contain transition-transform duration-200 group-hover:scale-105`}
        onError={(e) => {
          // Fallback if image fails to load
          e.currentTarget.src = '/setu-logo.png';
        }}
      />
      {showText && (
        <span className="text-xl font-bold tracking-tight text-current group-hover:text-sky-500 transition-colors">
          SETU
        </span>
      )}
    </div>
  );
};

export default AppLogo;
