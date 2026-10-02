import { Menu, Bell } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useTranslation } from '../i18n/LanguageContext';

export default function TopBar({ onMenuClick, title }) {
  const { t } = useTranslation();
  return (
    <header className="h-16 sticky top-0 z-20 flex items-center justify-between gap-4 px-4 sm:px-6 bg-white/80 dark:bg-slate-900/80 backdrop-blur border-b border-slate-200 dark:border-slate-800">
      <div className="flex items-center gap-3 min-w-0">
        <button onClick={onMenuClick} className="lg:hidden text-slate-500">
          <Menu size={22} />
        </button>
        <h1 className="text-base sm:text-lg font-semibold text-slate-900 dark:text-white truncate">{title}</h1>
      </div>
      <div className="flex items-center gap-2 sm:gap-3 shrink-0">
        <Link
          to="/app/registration"
          className="btn-primary hidden sm:inline-flex px-3.5 py-2 text-sm"
        >
          {t('newPatient')}
        </Link>
        <button className="relative h-9 w-9 rounded-full flex items-center justify-center text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800">
          <Bell size={18} />
        </button>
      </div>
    </header>
  );
}
