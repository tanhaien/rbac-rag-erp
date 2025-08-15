export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  roles: string[];
}

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

class AuthService {
  private baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  private tokenKey = 'rbac_rag_access_token';
  private refreshTokenKey = 'rbac_rag_refresh_token';

  // Get stored tokens
  getStoredTokens(): { accessToken: string | null; refreshToken: string | null } {
    const accessToken = localStorage.getItem(this.tokenKey);
    const refreshToken = localStorage.getItem(this.refreshTokenKey);
    return { accessToken, refreshToken };
  }

  // Store tokens
  storeTokens(accessToken: string, refreshToken?: string): void {
    localStorage.setItem(this.tokenKey, accessToken);
    if (refreshToken) {
      localStorage.setItem(this.refreshTokenKey, refreshToken);
    }
  }

  // Clear stored tokens
  clearTokens(): void {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.refreshTokenKey);
  }

  // Login
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Login failed');
    }

    return response.json();
  }

  // Get current user
  async getCurrentUser(): Promise<User> {
    const { accessToken } = this.getStoredTokens();
    if (!accessToken) {
      throw new Error('No access token available');
    }

    const response = await fetch(`${this.baseUrl}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to get user information');
    }

    return response.json();
  }

  // Refresh token
  async refreshToken(): Promise<LoginResponse> {
    const { refreshToken } = this.getStoredTokens();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await fetch(`${this.baseUrl}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${refreshToken}`,
      },
    });

    if (!response.ok) {
      throw new Error('Token refresh failed');
    }

    return response.json();
  }

  // Logout
  async logout(): Promise<void> {
    const { accessToken } = this.getStoredTokens();
    if (accessToken) {
      try {
        await fetch(`${this.baseUrl}/auth/revoke`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
          },
        });
      } catch (error) {
        // Ignore errors during logout
        console.warn('Error during logout:', error);
      }
    }

    this.clearTokens();
  }

  // Check if token is valid
  isTokenValid(token: string): boolean {
    if (!token) return false;
    
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Math.floor(Date.now() / 1000);
      return payload.exp > currentTime;
    } catch {
      return false;
    }
  }

  // Get authorization header
  getAuthHeader(): { Authorization: string } | {} {
    const { accessToken } = this.getStoredTokens();
    return accessToken ? { Authorization: `Bearer ${accessToken}` } : {};
  }
}

export const authService = new AuthService();
