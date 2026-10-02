import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, UserPlus, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { extractErrorMessage } from '../api/client';
import { useTranslation } from '../i18n/LanguageContext';

const ROLES = [
  { value: 'health_worker', label: 'Health Worker / Technician' },
  { value: 'ophthalmologist', label: 'Ophthalmologist / Doctor' },
];

export default function RegisterPage() {
  const { t } = useTranslation();
  const { register } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    phone: '',
    address: '',
    facility_name: '',
    district: '',
    role: 'health_worker',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const validate = () => {
    const next = {};
    if (!form.name || form.name.length < 2) next.name = 'Enter your full name';
    if (!form.email) next.email = t('required');
    if (!form.password || form.password.length < 8) next.password = 'Minimum 8 characters';
    if (!form.address) next.address = t('required');
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    try {
      await register(form);
      toast.success('Account created — welcome to RetinaScan!');
      navigate('/app/dashboard');
    } catch (err) {
      toast.error(extractErrorMessage(err, 'Could not create account.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 px-4 py-10">
      <div className="w-full max-w-lg">
        <div className="flex flex-col items-center mb-8">
          <div className="h-12 w-12 rounded-2xl bg-brand-600 flex items-center justify-center shadow-lg shadow-brand-600/20 mb-4">
            <UserPlus size={22} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{t('createAccount')}</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 text-center">{t('registerSubtitle')}</p>
        </div>

        <form onSubmit={handleSubmit} className="card p-7 space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 rounded-xl bg-slate-100 dark:bg-slate-800 p-1">
            {ROLES.map((r) => (
              <button
                key={r.value}
                type="button"
                onClick={() => setForm((f) => ({ ...f, role: r.value }))}
                className={`rounded-lg px-3 py-2 text-sm font-medium transition ${
                  form.role === r.value
                    ? 'bg-white dark:bg-slate-900 shadow-sm text-brand-700 dark:text-brand-400'
                    : 'text-slate-500 dark:text-slate-400'
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>

          <div>
            <label className="label">{t('fullName')}</label>
            <input className="input" placeholder="e.g. Priya Lakshmi" value={form.name} onChange={update('name')} />
            {errors.name && <p className="text-xs text-rose-600 mt-1">{errors.name}</p>}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="label">{t('email')}</label>
              <input type="email" className="input" placeholder="you@phc.gov.in" value={form.email} onChange={update('email')} />
              {errors.email && <p className="text-xs text-rose-600 mt-1">{errors.email}</p>}
            </div>
            <div>
              <label className="label">{t('phone')}</label>
              <input className="input" placeholder="98XXXXXXXX" value={form.phone} onChange={update('phone')} />
            </div>
          </div>

          <div>
            <label className="label">{t('password')}</label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                className="input pr-11"
                placeholder="At least 8 characters"
                value={form.password}
                onChange={update('password')}
              />
              <button
                type="button"
                onClick={() => setShowPassword((s) => !s)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
            {errors.password && <p className="text-xs text-rose-600 mt-1">{errors.password}</p>}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="label">{t('facilityName')}</label>
              <input
                className="input"
                placeholder="Primary Health Centre, ..."
                value={form.facility_name}
                onChange={update('facility_name')}
              />
            </div>
            <div>
              <label className="label">{t('district')}</label>
              <input className="input" placeholder="e.g. Villupuram" value={form.district} onChange={update('district')} />
            </div>
          </div>

          <div>
            <label className="label">{t('address')}</label>
            <textarea
              className="input min-h-[70px] resize-none"
              placeholder="Village / Taluk / District / State"
              value={form.address}
              onChange={update('address')}
            />
            {errors.address && <p className="text-xs text-rose-600 mt-1">{errors.address}</p>}
          </div>

          <button type="submit" disabled={loading} className="btn-primary w-full py-3">
            {loading ? <Loader2 size={18} className="animate-spin" /> : <UserPlus size={18} />}
            {t('createAccount')}
          </button>

          <p className="text-center text-sm text-slate-500 dark:text-slate-400">
            {t('alreadyHaveAccount')}{' '}
            <Link to="/login" className="text-brand-600 font-medium hover:underline">
              {t('signInHere')}
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
