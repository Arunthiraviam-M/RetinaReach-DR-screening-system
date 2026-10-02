import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '../api/endpoints';
import { MapPin, AlertTriangle } from 'lucide-react';
import { useTranslation } from '../i18n/LanguageContext';

export default function ReportsOverviewPage() {
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({
    queryKey: ['district-report'],
    queryFn: dashboardApi.districtReport,
  });

  const totalPatients = data?.reduce((sum, d) => sum + d.total_patients, 0) || 0;
  const totalReferable = data?.reduce((sum, d) => sum + d.referable_cases, 0) || 0;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div className="card p-5">
          <p className="text-2xl font-bold text-slate-900 dark:text-white">{totalPatients}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Total patients screened (all districts)</p>
        </div>
        <div className="card p-5">
          <p className="text-2xl font-bold text-rose-600">{totalReferable}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Referable DR cases (all districts)</p>
        </div>
      </div>

      <div className="card">
        <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-800">
          <h2 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
            <MapPin size={17} className="text-brand-500" /> {t('districtReport')}
          </h2>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-slate-400 text-sm">{t('loading')}</div>
        ) : !data?.length ? (
          <div className="p-10 text-center text-slate-400 text-sm">No data yet — register patients to populate this report.</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-slate-400 border-b border-slate-100 dark:border-slate-800">
                <th className="px-5 py-3 font-medium">District</th>
                <th className="px-5 py-3 font-medium text-right">Patients Screened</th>
                <th className="px-5 py-3 font-medium text-right">Referable Cases</th>
                <th className="px-5 py-3 font-medium text-right">Referral Rate</th>
              </tr>
            </thead>
            <tbody>
              {data.map((d) => (
                <tr key={d.district} className="border-b border-slate-50 dark:border-slate-800/60">
                  <td className="px-5 py-3.5 font-medium text-slate-800 dark:text-slate-100">{d.district}</td>
                  <td className="px-5 py-3.5 text-right text-slate-600 dark:text-slate-300">{d.total_patients}</td>
                  <td className="px-5 py-3.5 text-right">
                    <span className="inline-flex items-center gap-1 text-rose-600 font-medium">
                      {d.referable_cases > 0 && <AlertTriangle size={13} />}
                      {d.referable_cases}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-right text-slate-500 dark:text-slate-400">
                    {d.total_patients > 0 ? `${Math.round((d.referable_cases / d.total_patients) * 100)}%` : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
