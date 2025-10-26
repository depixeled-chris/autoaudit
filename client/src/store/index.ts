import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import authReducer from './slices/authSlice';
import { apiSlice } from './api/apiSlice';
import { projectsApi } from '@features/projects/projectsApi';
import { urlsApi } from '@features/urls/urlsApi';
import { checksApi } from '@features/checks/checksApi';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    [apiSlice.reducerPath]: apiSlice.reducer,
    [projectsApi.reducerPath]: projectsApi.reducer,
    [urlsApi.reducerPath]: urlsApi.reducer,
    [checksApi.reducerPath]: checksApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(apiSlice.middleware, projectsApi.middleware, urlsApi.middleware, checksApi.middleware),
});

// Enable refetchOnFocus/refetchOnReconnect behaviors
setupListeners(store.dispatch);

// Infer types from the store
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// Listen for auth:logout event from axios interceptor
window.addEventListener('auth:logout', () => {
  store.dispatch({ type: 'auth/logout' });
});

export default store;
