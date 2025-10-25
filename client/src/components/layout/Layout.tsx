import type { ReactNode } from 'react';
import { NavLink } from 'react-router-dom';
import { Folder, LogOut } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '@store/hooks';
import { logout } from '@store/slices/authSlice';
import { ThemeToggle } from '@components/ui/ThemeToggle';
import styles from './Layout.module.scss';

export interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const dispatch = useAppDispatch();
  const { user, isAuthenticated } = useAppSelector((state) => state.auth);

  const handleLogout = () => {
    dispatch(logout());
  };

  return (
    <div className={styles.layout}>
      <aside className={styles.sidebar}>
        <div className={styles.logo}>
          <h1>AutoAudit</h1>
          <p>Compliance Checker</p>
        </div>

        {user && (
          <div className={styles.userSection}>
            <div className={styles.user}>
              <div className={styles.userInfo}>
                <span className={styles.userName}>
                  {user.full_name || user.email}
                </span>
                {user.full_name && (
                  <span className={styles.userEmail}>{user.email}</span>
                )}
              </div>
            </div>

            <ThemeToggle />

            <button type="button" onClick={handleLogout} className={styles.logoutButton} title="Sign out">
              <LogOut size={20} />
              <span>Sign Out</span>
            </button>
          </div>
        )}

        <nav className={styles.nav}>
          {isAuthenticated && (
            <NavLink
              to="/projects"
              className={({ isActive }) =>
                `${styles.navItem} ${isActive ? styles.active : ''}`
              }
            >
              <Folder className={styles.navIcon} />
              <span>Projects</span>
            </NavLink>
          )}
        </nav>
      </aside>

      <main className={styles.main}>{children}</main>
    </div>
  );
}

export interface PageHeaderProps {
  title: string;
  description?: string;
}

export function PageHeader({ title, description }: PageHeaderProps) {
  return (
    <div className={styles.header}>
      <h1>{title}</h1>
      {description && <p>{description}</p>}
    </div>
  );
}
