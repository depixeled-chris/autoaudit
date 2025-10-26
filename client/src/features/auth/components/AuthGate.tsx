import { useEffect, useState, useRef } from 'react';
import type { ReactNode } from 'react';
import { useAppSelector, useAppDispatch } from '@store/hooks';
import { verifyToken } from '@store/slices/authSlice';

interface AuthGateProps {
  children: ReactNode;
}

/**
 * AuthGate - Verifies authentication status on mount
 * Attempts to restore session using refresh token cookie on page load
 * Blocks rendering until authentication check completes
 */
export function AuthGate({ children }: AuthGateProps) {
  const dispatch = useAppDispatch();
  const { isAuthenticated, isLoading } = useAppSelector((state) => state.auth);
  const [hasAttemptedAuth, setHasAttemptedAuth] = useState(false);
  const attemptedRef = useRef(false);

  useEffect(() => {
    // Prevent double execution in React StrictMode (development)
    // StrictMode intentionally runs effects twice which causes race conditions
    // with token rotation (first call revokes token, second call fails)
    if (attemptedRef.current) {
      return;
    }

    // On mount, always attempt to verify/restore authentication
    // This will try to use the refresh token cookie if available
    const attemptAuth = async () => {
      attemptedRef.current = true;
      await dispatch(verifyToken());
      setHasAttemptedAuth(true);
    };

    attemptAuth();
  }, [dispatch]);

  // Show loading state while verifying authentication on initial load
  if (!hasAttemptedAuth || isLoading) {
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
