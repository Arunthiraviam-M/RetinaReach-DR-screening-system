import { X, Sun, Moon, Monitor, Globe } from 'lucide-react';
import { useTranslation } from '../i18n/LanguageContext';
import { LANGUAGE_OPTIONS } from '../i18n/translations';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import clsx from 'clsx';

export default function SettingsModal({ open, onClose }) {
  const { t, language, setLanguage } = useTranslation();
  const { theme, setTheme } = useTheme();
  const { user, updatePreferences } = useAuth();
  const toast = useToast();

  if (!open) return null;

  const handleLanguageChange = async (code) => {
    setLanguage(code);
    if (user) {
      try {
        await updatePreferences({ preferred_language: code });
      } catch {
        /* best-effort sync; local preference already applied */
      }
    }
  };

  const handleThemeChange = async (value) => {
    setTheme(value);
    if (user) {
      try {
        await updatePreferences({ theme: value });
      } catch {
        /* best-effort sync */
      }
    }
    toast.info(`Theme set to ${value}`);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative w-full max-w-md card p-6 fade-in">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold text-slate-900 dark:text-white">{t('settings')}</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={20} />
          </button>
        </div>

        <div className="space-y-6">
          <div>
            <p className="label flex items-center gap-1.5">
              <Globe size={15} /> {t('language')}
            </p>
            <div className="grid grid-cols-3 gap-2">
              {LANGUAGE_OPTIONS.map((opt) => (
                <button
                  key={opt.code}
                  onClick={() => handleLanguageChange(opt.code)}
                  className={clsx(
                    'rounded-xl px-3 py-2.5 text-sm font-medium border transition',
                    language === opt.code
                      ? 'border-brand-500 bg-brand-50 text-brand-700 dark:bg-brand-950/50 dark:text-brand-300'
                      : 'border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'
                  )}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <p className="label">{t('theme')}</p>
            <div className="grid grid-cols-3 gap-2">
              {[
                { value: 'light', label: t('lightMode'), icon: Sun },
                { value: 'dark', label: t('darkMode'), icon: Moon },
                { value: 'system', label: t('systemMode'), icon: Monitor },
              ].map(({ value, label, icon: Icon }) => (
                <button
                  key={value}
                  onClick={() => handleThemeChange(value)}
                  className={clsx(
                    'flex flex-col items-center gap-1.5 rounded-xl px-3 py-3 text-xs font-medium border transition',
                    theme === value
                      ? 'border-brand-500 bg-brand-50 text-brand-700 dark:bg-brand-950/50 dark:text-brand-300'
                      : 'border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'
                  )}
                >
                  <Icon size={17} />
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="rounded-xl bg-slate-50 dark:bg-slate-800/60 p-4">
            <p className="label mb-2">{t('accountSettings')}</p>
            <dl className="text-sm space-y-1.5">
              <div className="flex justify-between">
                <dt className="text-slate-500 dark:text-slate-400">{t('fullName')}</dt>
                <dd className="font-medium text-slate-800 dark:text-slate-200">{user?.name}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500 dark:text-slate-400">{t('email')}</dt>
                <dd className="font-medium text-slate-800 dark:text-slate-200">{user?.email}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500 dark:text-slate-400">{t('role')}</dt>
                <dd className="font-medium text-slate-800 dark:text-slate-200 capitalize">
                  {user?.role?.replace('_', ' ')}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500 dark:text-slate-400">{t('district')}</dt>
                <dd className="font-medium text-slate-800 dark:text-slate-200">{user?.district || '-'}</dd>
              </div>
            </dl>
          </div>
        </div>

        <button onClick={onClose} className="btn-primary w-full mt-6">
          {t('close')}
        </button>
      </div>
    </div>
  );
}
