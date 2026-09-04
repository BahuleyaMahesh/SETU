import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthProvider';

interface RoleRouteProps {
  children: React.ReactNode;
  role: string;
}

const RoleRoute: React.FC<RoleRouteProps> = ({ children, role }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (user?.role !== role) {
    // Redirect based on user role
    if (user?.role === 'patient') {
      return <Navigate to="/patient/home" replace />;
    }
    if (user?.role === 'asha') {
      return <Navigate to="/asha/home" replace />;
    }
    if (user?.role === 'hospital') {
      return <Navigate to="/hospital/dashboard" replace />;
    }
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export default RoleRoute;
