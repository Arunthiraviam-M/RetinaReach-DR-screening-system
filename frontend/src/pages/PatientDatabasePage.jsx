import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Search, ChevronRight, User } from 'lucide-react';
import { patientsApi } from '../api/endpoints';
import { useTranslation } from '../i18n/LanguageContext';

export default function PatientDatabasePage() {
  const { t } = useTranslation();
  const [search, setSearch] = useState('');

  const { data: patients, isLoading } = useQuery({
    queryKey: ['patients', search],
    queryFn: () => patientsApi.list({ search: search || undefined }),
  });

  return (
    <div className="max-w-4xl mx-auto space-y-5">
      <div className="relative">
        <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          className="input pl-11 py-3"
          placeholder={t('searchPatient')}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="card divide-y divide-slate-100 dark:divide-slate-800">
        {isLoading ? (
          <div className="p-8 text-center text-slate-400 text-sm">{t('loading')}</div>
        ) : !patients?.length ? (
          <div className="p-10 text-center text-slate-400 text-sm">No patients found.</div>
        ) : (
          patients.map((p) => (
            <Link
              key={p.id}
              to={`/app/patients/${p.id}`}
              className="flex items-center justify-between px-5 py-4 hover:bg-slate-50 dark:hover:bg-slate-800/40 transition"
            >
              <div className="flex items-center gap-3.5">
                <div className="h-11 w-11 rounded-full bg-brand-50 dark:bg-brand-950/50 text-brand-700 dark:text-brand-300 flex items-center justify-center font-semibold">
                  <User size={18} />
                </div>
                <div>
                  <p className="font-medium text-slate-800 dark:text-slate-100">{p.full_name}</p>
                  <p className="text-xs text-slate-400">
                    {p.patient_code} · {p.age} yrs · {p.sex} · {p.village || p.district || '-'}
                  </p>
                </div>
              </div>
              <ChevronRight size={18} className="text-slate-300" />
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
