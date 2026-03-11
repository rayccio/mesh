import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authService, User } from '../services/authService';
import { orchestratorService } from '../services/orchestratorService';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  authError: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  changePassword: (oldPassword: string, newPassword: string) => Promise<void>;
  hasRole: (role: string | string[]) => boolean;
  refreshUser: () => Promise<void>;
  refreshGatewayState: () => Promise<void>;
  gatewayEnabled: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState<string | null>(null);
  const [gatewayEnabled, setGatewayEnabled] = useState(true);

  const refreshGatewayState = async () => {
    try {
      const enabled = await orchestratorService.getGatewayState();
      setGatewayEnabled(enabled);
    } catch (err) {
      console.error('Failed to refresh gateway state', err);
      setGatewayEnabled(false);
    }
  };

  useEffect(() => {
    const initAuth = async () => {
      try {
        // Fetch current gateway state directly (avoid stale closure)
        const enabled = await orchestratorService.getGatewayState();
        setGatewayEnabled(enabled);

        if (enabled) {
          // Gateway enabled – check for existing session
          const storedUser = authService.getUser();
          const token = authService.getToken();
          
          if (storedUser && token) {
            try {
              const freshUser = await orchestratorService.getCurrentUser();
              setUser({
                id: freshUser.id,
                username: freshUser.username,
                role: freshUser.role,
                assignedHiveIds: freshUser.assignedHiveIds,
                password_changed: freshUser.password_changed || false,
                createdAt: freshUser.createdAt,
                lastLogin: freshUser.lastLogin
              });
              authService.initTimeoutListener();
              setAuthError(null);
            } catch (error) {
              authService.logout();
              setUser(null);
              setAuthError('Session expired. Please log in again.');
            }
          } else {
            setUser(null);
            setAuthError(null);
          }
        } else {
          // Gateway disabled – auto‑login with the special no‑auth token
          try {
            const response = await authService.getNoAuthToken();
            setUser({
              id: response.user_id,
              username: response.username,
              role: response.role,
              assignedHiveIds: [],
              password_changed: response.password_changed,
              createdAt: new Date().toISOString()
            });
            setAuthError(null);
          } catch (error) {
            console.error('Auto-login failed:', error);
            setAuthError('Failed to connect to backend. Please check server status.');
            setUser(null);
          }
        }
      } catch (error) {
        console.error('Auth initialization failed:', error);
        setAuthError('Failed to initialize authentication.');
      } finally {
        setLoading(false);
      }
    };

    initAuth();

    return () => {
      authService.cleanup();
    };
  }, []); // run once on mount

  const login = async (username: string, password: string) => {
    const response = await authService.login(username, password);
    setUser({
      id: response.user_id,
      username: response.username,
      role: response.role,
      assignedHiveIds: [],
      password_changed: response.password_changed,
      createdAt: new Date().toISOString()
    });
    setAuthError(null);
  };

  const logout = () => {
    authService.logout();
    setUser(null);
  };

  const changePassword = async (oldPassword: string, newPassword: string) => {
    await authService.changePassword(oldPassword, newPassword);
    if (user) {
      user.password_changed = true;
      setUser({ ...user });
    }
  };

  const hasRole = (role: string | string[]): boolean => {
    return authService.hasRole(role);
  };

  const refreshUser = async () => {
    await authService.refreshUser();
    const updatedUser = authService.getUser();
    setUser(updatedUser);
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      authError,
      login,
      logout,
      changePassword,
      hasRole,
      refreshUser,
      refreshGatewayState,
      gatewayEnabled
    }}>
      {children}
    </AuthContext.Provider>
  );
};
