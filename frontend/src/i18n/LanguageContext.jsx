import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { translations } from './translations';

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(() => localStorage.getItem('retinascan_lang') || 'en');

  const setLanguage = useCallback((lang) => {
    setLanguageState(lang);
    localStorage.setItem('retinascan_lang', lang);
  }, []);

  const t = useCallback(
    (key) => {
      return translations[language]?.[key] ?? translations.en[key] ?? key;
    },
    [language]
  );

  const value = useMemo(() => ({ language, setLanguage, t }), [language, setLanguage, t]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useTranslation() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useTranslation must be used within LanguageProvider');
  return ctx;
}
