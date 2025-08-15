import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { authService, AuthState, User, LoginRequest } from '../services/authService';

interface AuthContextType extends AuthState {
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

type AuthAction =
  | { type: 'AUTH_START' }
  | { type: 'AUTH_SUCCESS'; payload: { user: User; accessToken: string; refreshToken?: string } }
  | { type: 'AUTH_FAILURE' }
  | { type: 'AUTH_LOGOUT' }
  | { type: 'AUTH_REFRESH'; payload: { accessToken: string; refreshToken?: string } };

const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'AUTH_START':
      return { ...state, isLoading: true };
    case 'AUTH_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        accessToken: action.payload.accessToken,
        refreshToken: action.payload.refreshToken || null,
        isAuthenticated: true,
        isLoading: false,
      };
    case 'AUTH_FAILURE':
      return {
        ...state,
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
      };
    case 'AUTH_LOGOUT':
      return {
        ...state,
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
      };
    case 'AUTH_REFRESH':
      return {
        ...state,
        accessToken: action.payload.accessToken,
        refreshToken: action.payload.refreshToken || state.refreshToken,
        isLoading: false,
      };
    default:
      return state;
  }
};

const initialState: AuthState = {
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: true,
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Initialize authentication state on app load
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const { accessToken, refreshToken } = authService.getStoredTokens();
        
        if (accessToken && authService.isTokenValid(accessToken)) {
          const user = await authService.getCurrentUser();
          dispatch({
            type: 'AUTH_SUCCESS',
            payload: { user, accessToken, refreshToken: refreshToken || undefined },
          });
        } else if (refreshToken) {
          // Try to refresh the token
          await refreshAuth();
        } else {
          dispatch({ type: 'AUTH_FAILURE' });
        }
      } catch (error) {
        console.error('Auth initialization failed:', error);
        dispatch({ type: 'AUTH_FAILURE' });
      }
    };

    initializeAuth();
  }, []);

  const login = async (credentials: LoginRequest) => {
    dispatch({ type: 'AUTH_START' });
    
    try {
      const response = await authService.login(credentials);
      authService.storeTokens(response.access_token, response.refresh_token);
      
      const user = await authService.getCurrentUser();
      dispatch({
        type: 'AUTH_SUCCESS',
        payload: {
          user,
          accessToken: response.access_token,
          refreshToken: response.refresh_token,
        },
      });
    } catch (error) {
      console.error('Login failed:', error);
      dispatch({ type: 'AUTH_FAILURE' });
      throw error;
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      dispatch({ type: 'AUTH_LOGOUT' });
    }
  };

  const refreshAuth = async () => {
    try {
      const response = await authService.refreshToken();
      authService.storeTokens(response.access_token, response.refresh_token);
      
      dispatch({
        type: 'AUTH_REFRESH',
        payload: {
          accessToken: response.access_token,
          refreshToken: response.refresh_token,
        },
      });
    } catch (error) {
      console.error('Token refresh failed:', error);
      dispatch({ type: 'AUTH_FAILURE' });
      throw error;
    }
  };

  const value: AuthContextType = {
    ...state,
    login,
    logout,
    refreshAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
