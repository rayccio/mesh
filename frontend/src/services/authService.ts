import { orchestratorService } from './orchestratorService';

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  username: string;
  role: string;
  password_changed: boolean;
  gateway_enabled: boolean;
}

export interface User {
  id: string;
  username: string;
  role: string;
  assignedHiveIds: string[];
  password_changed: boolean;
  createdAt: string;
  lastLogin?: string;
}

class AuthService {
  private tokenKey = 'hivebot_token';
  private userKey = 'hivebot_user';
  private timeoutKey = 'hivebot_timeout';
  private timeoutDuration = 30 * 60 * 1000; // 30 minutes default

  async login(username: string, password: string): Promise<LoginResponse> {
    try {
      const response = await orchestratorService.login(username, password);
      this.setToken(response.access_token);
      this.setUser({
        id: response.user_id,
        username: response.username,
        role: response.role,
        assignedHiveIds: [],
        password_changed: response.password_changed,
        createdAt: new Date().toISOString()
      });
      this.resetTimeout();
      return response;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  }

  async getNoAuthToken(): Promise<LoginResponse> {
    try {
      const response = await orchestratorService.getNoAuthToken();
      this.setToken(response.access_token);
      this.setUser({
        id: response.user_id,
        username: response.username,
        role: response.role,
        assignedHiveIds: [],
        password_changed: response.password_changed,
        createdAt: new Date().toISOString()
      });
      this.resetTimeout();
      return response;
    } catch (error) {
      console.error('No-auth token fetch failed:', error);
      throw error;
    }
  }

  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    await orchestratorService.changePassword(oldPassword, newPassword);
    // Update user's password_changed flag
    const user = this.getUser();
    if (user) {
      user.password_changed = true;
      this.setUser(user);
    }
  }

  logout(): void {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.userKey);
    localStorage.removeItem(this.timeoutKey);
    window.location.href = '/login';
  }

  setToken(token: string): void {
    localStorage.setItem(this.tokenKey, token);
  }

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  setUser(user: User): void {
    localStorage.setItem(this.userKey, JSON.stringify(user));
  }

  getUser(): User | null {
    const userStr = localStorage.getItem(this.userKey);
    if (!userStr) return null;
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  }

  isAuthenticated(): boolean {
    const token = this.getToken();
    const user = this.getUser();
    return !!(token && user);
  }

  hasRole(requiredRole: string | string[]): boolean {
    const user = this.getUser();
    if (!user) return false;
    
    if (Array.isArray(requiredRole)) {
      return requiredRole.includes(user.role);
    }
    return user.role === requiredRole;
  }

  resetTimeout(): void {
    const expiry = Date.now() + this.timeoutDuration;
    localStorage.setItem(this.timeoutKey, expiry.toString());
  }

  checkTimeout(): boolean {
    const expiryStr = localStorage.getItem(this.timeoutKey);
    if (!expiryStr) return true;
    
    const expiry = parseInt(expiryStr, 10);
    if (Date.now() > expiry) {
      this.logout();
      return false;
    }
    return true;
  }

  async refreshUser(): Promise<void> {
    try {
      const user = await orchestratorService.getCurrentUser();
      this.setUser({
        id: user.id,
        username: user.username,
        role: user.role,
        assignedHiveIds: user.assignedHiveIds || [],
        password_changed: user.password_changed || false,
        createdAt: user.createdAt,
        lastLogin: user.lastLogin
      });
    } catch (error) {
      console.error('Failed to refresh user:', error);
      this.logout();
    }
  }

  // Session timeout auto-refresh
  initTimeoutListener(): void {
    const checkInterval = setInterval(() => {
      if (this.isAuthenticated()) {
        this.checkTimeout();
      }
    }, 60000); // Check every minute
    
    // Store interval ID for cleanup
    (window as any).__timeoutInterval = checkInterval;
  }

  cleanup(): void {
    if ((window as any).__timeoutInterval) {
      clearInterval((window as any).__timeoutInterval);
    }
  }
}

export const authService = new AuthService();
