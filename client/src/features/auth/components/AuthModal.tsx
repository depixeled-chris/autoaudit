import { useState, useEffect, useRef } from 'react';
import type { FormEvent } from 'react';
import { useAppDispatch, useAppSelector } from '@store/hooks';
import { login, register, clearError } from '@store/slices/authSlice';
import { useModal } from '@contexts/ModalContext';
import { Modal } from '@components/ui/Modal';
import { Button } from '@components/ui/Button';
import styles from './AuthModal.module.scss';

export function AuthModal() {
  const { currentModal, closeModal, openModal } = useModal();
  const dispatch = useAppDispatch();
  const { isLoading, error, isAuthenticated } = useAppSelector((state) => state.auth);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const hasAutoOpened = useRef(false);

  const isLogin = currentModal === 'login';
  const isRegister = currentModal === 'register';

  const resetForm = () => {
    setEmail('');
    setPassword('');
    setFullName('');
    dispatch(clearError());
  };

  const handleClose = () => {
    resetForm();
    closeModal();
  };

  // Auto-open login modal if not authenticated (only once)
  useEffect(() => {
    if (!isAuthenticated && !isLoading && !currentModal && !hasAutoOpened.current) {
      openModal('login');
      hasAutoOpened.current = true;
    }
  }, [isAuthenticated, isLoading, currentModal]);

  // Close modal on successful authentication
  useEffect(() => {
    if (isAuthenticated && (isLogin || isRegister)) {
      handleClose();
    }
  }, [isAuthenticated]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    dispatch(clearError());

    if (isLogin) {
      dispatch(login({ email, password }));
    } else {
      dispatch(register({ email, password, full_name: fullName || undefined }));
    }
  };

  const switchMode = () => {
    resetForm();
    openModal(isLogin ? 'register' : 'login');
  };

  return (
    <Modal
      isOpen={isLogin || isRegister}
      onClose={handleClose}
      title={isLogin ? 'Sign In' : 'Create Account'}
      size="small"
    >
      <form onSubmit={handleSubmit} className={styles.form}>
        {error && <div className={styles.error}>{error}</div>}

        {isRegister && (
          <div className={styles.field}>
            <label htmlFor="fullName">Full Name (Optional)</label>
            <input
              id="fullName"
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              autoComplete="name"
              disabled={isLoading}
            />
          </div>
        )}

        <div className={styles.field}>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
            disabled={isLoading}
            autoFocus
          />
        </div>

        <div className={styles.field}>
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete={isLogin ? 'current-password' : 'new-password'}
            disabled={isLoading}
            minLength={8}
          />
        </div>

        <Button type="submit" variant="primary" fullWidth disabled={isLoading}>
          {isLoading
            ? isLogin
              ? 'Signing in...'
              : 'Creating account...'
            : isLogin
            ? 'Sign In'
            : 'Create Account'}
        </Button>

        <div className={styles.footer}>
          {isLogin ? (
            <>
              Don't have an account?{' '}
              <button type="button" onClick={switchMode} className={styles.link}>
                Sign up
              </button>
            </>
          ) : (
            <>
              Already have an account?{' '}
              <button type="button" onClick={switchMode} className={styles.link}>
                Sign in
              </button>
            </>
          )}
        </div>
      </form>
    </Modal>
  );
}
