import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  UserPlus2,
  Users,
  GaugeCircle,
  FileBarChart2,
  Settings as SettingsIcon,
  LogOut,
  Eye,
  X,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTranslation } from '../i18n/LanguageContext';
import clsx from 'clsx';

export default function Sidebar({ open, onClose, onOpenSettings }) {
  const { user, logout } = useAuth();
  const { t } = useTranslation();

  const navItems = [
    { to: '/app/dashboard', icon: LayoutDashboard, label: t('dashboard') },
    { to: '/app/registration', icon: UserPlus2, label: t('newRegistration') },
    { to: '/app/patients', icon: Users, label: t('patientDatabase') },
    { to: '/app/simulation', icon: GaugeCircle, label: t('workflowSimulation') },
    { to: '/app/reports', icon: FileBarChart2, label: t('districtReport') },
  ];

  return (
    <>
      {open && <div className="fixed inset-0 bg-black/40 z-30 lg:hidden" onClick={onClose} />}
      <aside
        className={clsx(
          'fixed lg:sticky top-0 z-40 h-screen w-72 shrink-0 flex flex-col bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 transition-transform duration-200',
          open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        <div className="flex items-center justify-between px-5 h-16 border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-lg bg-brand-600 flex items-center justify-center">
              <Eye size={17} className="text-white" />
            </div>
            <span className="font-bold text-slate-900 dark:text-white tracking-tight">{t('appName')}</span>
          </div>
          <button onClick={onClose} className="lg:hidden text-slate-400">
            <X size={20} />
          </button>
        </div>

        <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-brand-100 dark:bg-brand-900 flex items-center justify-center text-brand-700 dark:text-brand-300 font-semibold text-sm shrink-0">
              {user?.name?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 truncate">{user?.name}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400 truncate capitalize">
                {user?.role?.replace('_', ' ')}
              </p>
            </div>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              onClick={onClose}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-brand-50 text-brand-700 dark:bg-brand-950/60 dark:text-brand-300'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
                )
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-3 py-4 border-t border-slate-200 dark:border-slate-800 space-y-1">
          <button
            onClick={onOpenSettings}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <SettingsIcon size={18} />
            {t('settings')}
          </button>
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors"
          >
            <LogOut size={18} />
            {t('logout')}
          </button>
        </div>
      </aside>
    </>
  );
}
