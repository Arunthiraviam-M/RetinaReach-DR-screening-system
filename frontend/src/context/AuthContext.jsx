import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { authApi } from '../api/endpoints';
import { setTokens } from '../api/client';
import { useTranslation } from '../i18n/LanguageContext';
import { useTheme } from './ThemeContext';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('retinascan_user') || 'null');
    } catch {
      return null;
    }
  });
  const [initializing, setInitializing] = useState(true);
  const { setLanguage } = useTranslation();
  const { setTheme } = useTheme();

  const persistUser = useCallback(
    (u) => {
      setUser(u);
      if (u) {
        localStorage.setItem('retinascan_user', JSON.stringify(u));
        if (u.preferred_language) setLanguage(u.preferred_language);
        if (u.theme) setTheme(u.theme);
      } else {
        localStorage.removeItem('retinascan_user');
      }
    },
    [setLanguage, setTheme]
  );

  useEffect(() => {
    // Verify token is still valid on load; if not, session is cleared silently.
    const hasTokens = localStorage.getItem('retinascan_tokens');
    if (!hasTokens) {
      setInitializing(false);
      return;
    }
    authApi
      .me()
      .then((u) => persistUser(u))
      .catch(() => {
        setTokens(null);
        persistUser(null);
      })
      .finally(() => setInitializing(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = useCallback(
    async (email, password) => {
      const data = await authApi.login({ email, password });
      setTokens(data.tokens);
      persistUser(data.user);
      return data.user;
    },
    [persistUser]
  );

  const register = useCallback(
    async (payload) => {
      const data = await authApi.register(payload);
      setTokens(data.tokens);
      persistUser(data.user);
      return data.user;
    },
    [persistUser]
  );

  const logout = useCallback(() => {
    setTokens(null);
    persistUser(null);
  }, [persistUser]);

  const updatePreferences = useCallback(
    async (payload) => {
      const updated = await authApi.updatePreferences(payload);
      persistUser(updated);
      return updated;
    },
    [persistUser]
  );

  const value = useMemo(
    () => ({ user, initializing, login, register, logout, updatePreferences }),
    [user, initializing, login, register, logout, updatePreferences]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
