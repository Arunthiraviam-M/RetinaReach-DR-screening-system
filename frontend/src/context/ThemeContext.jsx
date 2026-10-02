import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

const ThemeContext = createContext(null);

function applyThemeClass(theme) {
  const root = document.documentElement;
  const resolved =
    theme === 'system'
      ? window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light'
      : theme;
  root.classList.toggle('dark', resolved === 'dark');
}

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(() => localStorage.getItem('retinascan_theme') || 'light');

  useEffect(() => {
    applyThemeClass(theme);
    if (theme === 'system') {
      const mq = window.matchMedia('(prefers-color-scheme: dark)');
      const listener = () => applyThemeClass('system');
      mq.addEventListener('change', listener);
      return () => mq.removeEventListener('change', listener);
    }
  }, [theme]);

  const setTheme = useCallback((value) => {
    setThemeState(value);
    localStorage.setItem('retinascan_theme', value);
  }, []);

  const value = useMemo(() => ({ theme, setTheme }), [theme, setTheme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}
