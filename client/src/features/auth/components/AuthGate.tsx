import { useEffect } from 'react';
import type { ReactNode } from 'react';
import { useAppSelector, useAppDispatch } from '@store/hooks';
import { verifyToken } from '@store/slices/authSlice';

interface AuthGateProps {
  children: ReactNode;
}

/**
 * AuthGate - Verifies authentication status on mount
 * Does NOT block rendering - just ensures auth state is verified
 */
export function AuthGate({ children }: AuthGateProps) {
  const dispatch = useAppDispatch();
  const { token, isAuthenticated, isLoading } = useAppSelector((state) => state.auth);

  useEffect(() => {
    // If we have a token but haven't verified it yet, verify it
    if (token && !isAuthenticated && !isLoading) {
      dispatch(verifyToken());
    }
  }, [token, isAuthenticated, isLoading, dispatch]);

  // Show loading state while verifying initial token
  if (token && !isAuthenticated && isLoading) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          color: 'var(--color-text-secondary)',
        }}
      >
        Verifying authentication...
      </div>
    );
  }

  return <>{children}</>;
}
