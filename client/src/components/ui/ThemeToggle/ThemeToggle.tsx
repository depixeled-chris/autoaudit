import { Sun, Moon, Monitor } from 'lucide-react';
import { useTheme } from '@contexts/ThemeContext';
import styles from './ThemeToggle.module.scss';

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  const toggleTheme = () => {
    const themes: ('system' | 'light' | 'dark')[] = ['system', 'light', 'dark'];
    const currentIndex = themes.indexOf(theme);
    const nextIndex = (currentIndex + 1) % themes.length;
    setTheme(themes[nextIndex]);
  };

  const getIcon = () => {
    switch (theme) {
      case 'light':
        return <Sun size={20} />;
      case 'dark':
        return <Moon size={20} />;
      default:
        return <Monitor size={20} />;
    }
  };

  const getLabel = () => {
    switch (theme) {
      case 'light':
        return 'Light';
      case 'dark':
        return 'Dark';
      default:
        return 'System';
    }
  };

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={styles.toggle}
      title={`Current theme: ${getLabel()}`}
      aria-label="Toggle theme"
    >
      {getIcon()}
      <span className={styles.label}>{getLabel()}</span>
    </button>
  );
}
