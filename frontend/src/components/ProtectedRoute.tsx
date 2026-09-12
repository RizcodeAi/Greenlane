import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../store/auth';

interface Props { children: React.ReactNode; roles?: string[]; }

export default function ProtectedRoute({ children, roles }: Props) {
  const { isAuthenticated, user } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (roles && roles.length > 0 && user && !roles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }
  return <>{children}</>;
}
