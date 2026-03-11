import React, { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LoadingSpinner } from './LoadingSpinner';

interface ProtectedRouteProps {
  children: ReactNode;
  requiredRole?: string | string[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredRole 
}) => {
  const { user, loading, hasRole, gatewayEnabled, authError } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (authError) {
    return (
      <div className="text-center py-12 text-red-400">
        {authError}
      </div>
    );
  }

  // If gateway is disabled, we assume auto-login succeeded, so user should exist.
  // If not (shouldn't happen because authError would be set), show error.
  if (!gatewayEnabled && !user) {
    return (
      <div className="text-center py-12 text-red-400">
        Failed to initialize. Please check backend connection.
      </div>
    );
  }

  // If gateway is enabled and no user, go to login
  if (gatewayEnabled && !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check role requirements
  if (requiredRole && !hasRole(requiredRole)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <>{children}</>;
};
