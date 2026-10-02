import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Users, UserPlus, Clock, CheckCircle2, AlertTriangle, ChevronRight } from 'lucide-react';
import { dashboardApi } from '../api/endpoints';
import { useTranslation } from '../i18n/LanguageContext';

function StatCard({ icon: Icon, label, value, tone }) {
  const tones = {
    brand: 'bg-brand-50 text-brand-700 dark:bg-brand-950/50 dark:text-brand-300',
    amber: 'bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300',
    emerald: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300',
    rose: 'bg-rose-50 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300',
  };
  return (
    <div className="card p-5 flex items-center gap-4">
      <div className={`h-11 w-11 rounded-xl flex items-center justify-center shrink-0 ${tones[tone]}`}>
        <Icon size={20} />
      </div>
      <div>
        <p className="text-2xl font-bold text-slate-900 dark:text-white leading-none">{value}</p>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1.5">{label}</p>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => dashboardApi.get(15),
    refetchInterval: 30000,
  });

  const stats = data?.stats;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard icon={Users} label={t('totalPatients')} value={stats?.total_patients ?? '—'} tone="brand" />
        <StatCard icon={UserPlus} label={t('patientsToday')} value={stats?.patients_today ?? '—'} tone="brand" />
        <StatCard icon={Clock} label={t('pendingReview')} value={stats?.studies_pending_review ?? '—'} tone="amber" />
        <StatCard icon={CheckCircle2} label={t('analyzedToday')} value={stats?.studies_analyzed_today ?? '—'} tone="emerald" />
        <StatCard icon={AlertTriangle} label={t('referableToday')} value={stats?.referable_cases_today ?? '—'} tone="rose" />
      </div>

      <div className="card">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-slate-800">
          <h2 className="font-semibold text-slate-900 dark:text-white">{t('recentArrivals')}</h2>
          <Link to="/app/patients" className="text-sm text-brand-600 font-medium hover:underline flex items-center gap-1">
            {t('viewHistory')} <ChevronRight size={15} />
          </Link>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-slate-400 text-sm">{t('loading')}</div>
        ) : !data?.recent_arrivals?.length ? (
          <div className="p-10 text-center text-slate-400 text-sm">{t('noArrivalsYet')}</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-400 border-b border-slate-100 dark:border-slate-800">
                  <th className="px-5 py-3 font-medium">Patient</th>
                  <th className="px-5 py-3 font-medium">Village / District</th>
                  <th className="px-5 py-3 font-medium">{t('date')}</th>
                  <th className="px-5 py-3 font-medium">{t('status')}</th>
                  <th className="px-5 py-3 font-medium text-right">{t('actions')}</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_arrivals.map((a) => (
                  <tr
                    key={a.study_id}
                    className="border-b border-slate-50 dark:border-slate-800/60 hover:bg-slate-50 dark:hover:bg-slate-800/40 transition"
                  >
                    <td className="px-5 py-3.5">
                      <p className="font-medium text-slate-800 dark:text-slate-100">{a.patient_name}</p>
                      <p className="text-xs text-slate-400">{a.patient_code}</p>
                    </td>
                    <td className="px-5 py-3.5 text-slate-500 dark:text-slate-400">
                      {a.village || '-'}{a.district ? `, ${a.district}` : ''}
                    </td>
                    <td className="px-5 py-3.5 text-slate-500 dark:text-slate-400">
                      {new Date(a.arrival_time).toLocaleString(undefined, {
                        day: '2-digit',
                        month: 'short',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>
                    <td className="px-5 py-3.5">
                      {a.dr_grade_label ? (
                        <span className={`badge ${a.referable_dr ? 'bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300' : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300'}`}>
                          {a.dr_grade_label}
                        </span>
                      ) : (
                        <span className="badge bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400 capitalize">
                          {a.status.replace('_', ' ')}
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <Link
                        to={`/app/patients/${a.patient_id}`}
                        className="text-brand-600 font-medium hover:underline text-sm"
                      >
                        {t('viewHistory')}
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
