import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import apiClient from '@lib/api/axios';

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
}

interface AuthState {
  user: User | null;
  token: string | null;  // Stored in memory only (not localStorage)
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
  tokenExpiresAt: number | null;  // Timestamp for auto-refresh
}

const initialState: AuthState = {
  user: null,
  token: null,  // No longer initialized from localStorage
  isLoading: false,
  isAuthenticated: false,
  error: null,
  tokenExpiresAt: null,
};

// Async thunks
export const login = createAsyncThunk(
  'auth/login',
  async ({ email, password }: { email: string; password: string }, { rejectWithValue }) => {
    try {
      const response = await apiClient.post('/api/auth/login', { email, password }, {
        withCredentials: true,  // Include cookies for refresh token
      });
      const { access_token, user } = response.data;

      // Calculate token expiration (15 minutes from now)
      const tokenExpiresAt = Date.now() + 15 * 60 * 1000;

      return { token: access_token, user, tokenExpiresAt };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Login failed');
    }
  }
);

export const register = createAsyncThunk(
  'auth/register',
  async (
    { email, password, full_name }: { email: string; password: string; full_name?: string },
    { rejectWithValue }
  ) => {
    try {
      const response = await apiClient.post('/api/auth/register', { email, password, full_name }, {
        withCredentials: true,  // Include cookies for refresh token
      });
      const { access_token, user } = response.data;

      // Calculate token expiration (15 minutes from now)
      const tokenExpiresAt = Date.now() + 15 * 60 * 1000;

      return { token: access_token, user, tokenExpiresAt };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Registration failed');
    }
  }
);

export const refreshToken = createAsyncThunk(
  'auth/refreshToken',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.post('/api/auth/refresh', {}, {
        withCredentials: true,  // Send refresh token cookie
      });
      const { access_token, user } = response.data;

      // Calculate token expiration (15 minutes from now)
      const tokenExpiresAt = Date.now() + 15 * 60 * 1000;

      return { token: access_token, user, tokenExpiresAt };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Token refresh failed');
    }
  }
);

export const verifyToken = createAsyncThunk(
  'auth/verifyToken',
  async (_, { rejectWithValue, dispatch }) => {
    try {
      // First try to refresh the token (will use refresh token cookie)
      const refreshResult = await dispatch(refreshToken());
      if (refreshToken.fulfilled.match(refreshResult)) {
        return refreshResult.payload.user;
      }
      return rejectWithValue('Token verification failed');
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Token verification failed');
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout: (state) => {
      // Call logout API endpoint to revoke refresh token
      apiClient.post('/api/auth/logout', {}, {
        withCredentials: true,
      }).catch(() => {
        // Ignore errors - user is logging out anyway
      });

      state.user = null;
      state.token = null;
      state.isAuthenticated = false;
      state.error = null;
      state.tokenExpiresAt = null;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Login
    builder
      .addCase(login.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.isLoading = false;
        state.isAuthenticated = true;
        state.token = action.payload.token;
        state.user = action.payload.user;
        state.tokenExpiresAt = action.payload.tokenExpiresAt;
        state.error = null;
      })
      .addCase(login.rejected, (state, action) => {
        state.isLoading = false;
        state.isAuthenticated = false;
        state.error = action.payload as string;
      });

    // Register
    builder
      .addCase(register.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(register.fulfilled, (state, action) => {
        state.isLoading = false;
        state.isAuthenticated = true;
        state.token = action.payload.token;
        state.user = action.payload.user;
        state.tokenExpiresAt = action.payload.tokenExpiresAt;
        state.error = null;
      })
      .addCase(register.rejected, (state, action) => {
        state.isLoading = false;
        state.isAuthenticated = false;
        state.error = action.payload as string;
      });

    // Refresh Token
    builder
      .addCase(refreshToken.fulfilled, (state, action) => {
        state.token = action.payload.token;
        state.user = action.payload.user;
        state.tokenExpiresAt = action.payload.tokenExpiresAt;
        state.isAuthenticated = true;
      })
      .addCase(refreshToken.rejected, (state) => {
        // Refresh failed - logout user
        state.user = null;
        state.token = null;
        state.tokenExpiresAt = null;
        state.isAuthenticated = false;
      });

    // Verify Token
    builder
      .addCase(verifyToken.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(verifyToken.fulfilled, (state, action) => {
        state.isLoading = false;
        state.isAuthenticated = true;
        state.user = action.payload;
      })
      .addCase(verifyToken.rejected, (state) => {
        state.isLoading = false;
        state.isAuthenticated = false;
        state.user = null;
        state.token = null;
        state.tokenExpiresAt = null;
      });
  },
});

export const { logout, clearError } = authSlice.actions;
export default authSlice.reducer;

// Selector to get the current token
export const selectAuthToken = (state: { auth: AuthState }) => state.auth.token;
