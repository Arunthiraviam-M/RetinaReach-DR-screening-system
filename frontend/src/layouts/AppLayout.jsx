import { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import TopBar from '../components/TopBar';
import SettingsModal from '../components/SettingsModal';
import { useTranslation } from '../i18n/LanguageContext';

const TITLE_KEYS = {
  '/app/dashboard': 'dashboard',
  '/app/registration': 'newRegistration',
  '/app/patients': 'patientDatabase',
  '/app/simulation': 'workflowSimulation',
  '/app/reports': 'districtReport',
};

export default function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const { t } = useTranslation();
  const location = useLocation();

  const titleKey = TITLE_KEYS[location.pathname];
  const title = titleKey ? t(titleKey) : t('appName');

  return (
    <div className="min-h-screen flex bg-slate-50 dark:bg-slate-950">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} onOpenSettings={() => setSettingsOpen(true)} />
      <div className="flex-1 min-w-0 flex flex-col">
        <TopBar onMenuClick={() => setSidebarOpen(true)} title={title} />
        <main className="flex-1 p-4 sm:p-6 max-w-[1400px] w-full mx-auto">
          <Outlet />
        </main>
      </div>
      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
}
