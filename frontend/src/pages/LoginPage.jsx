import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, LogIn, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { extractErrorMessage } from '../api/client';
import { useTranslation } from '../i18n/LanguageContext';

export default function LoginPage() {
  const { t } = useTranslation();
  const { login } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();

  const [form, setForm] = useState({ email: '', password: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const validate = () => {
    const next = {};
    if (!form.email) next.email = t('required');
    if (!form.password) next.password = t('required');
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    try {
      await login(form.email, form.password);
      toast.success('Welcome back!');
      navigate('/app/dashboard');
    } catch (err) {
      toast.error(extractErrorMessage(err, 'Invalid email or password.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 px-4 py-10">
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center mb-8">
          <div className="h-12 w-12 rounded-2xl bg-brand-600 flex items-center justify-center shadow-lg shadow-brand-600/20 mb-4">
            <Eye size={24} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{t('welcomeBack')}</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{t('signInSubtitle')}</p>
        </div>

        <form onSubmit={handleSubmit} className="card p-7 space-y-5">
          <div>
            <label className="label">{t('email')}</label>
            <input
              type="email"
              className="input"
              placeholder="you@healthcentre.gov.in"
              value={form.email}
              onChange={update('email')}
              autoComplete="email"
            />
            {errors.email && <p className="text-xs text-rose-600 mt-1">{errors.email}</p>}
          </div>

          <div>
            <label className="label">{t('password')}</label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                className="input pr-11"
                placeholder="••••••••"
                value={form.password}
                onChange={update('password')}
                autoComplete="current-password"
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

          <button type="submit" disabled={loading} className="btn-primary w-full py-3">
            {loading ? <Loader2 size={18} className="animate-spin" /> : <LogIn size={18} />}
            {t('login')}
          </button>

          <p className="text-center text-sm text-slate-500 dark:text-slate-400">
            {t('dontHaveAccount')}{' '}
            <Link to="/register" className="text-brand-600 font-medium hover:underline">
              {t('registerHere')}
            </Link>
          </p>
        </form>

        <div className="mt-6 rounded-xl bg-brand-50 dark:bg-brand-950/40 border border-brand-100 dark:border-brand-900 p-4 text-xs text-brand-800 dark:text-brand-300">
          <p className="font-semibold mb-1">Demo accounts (after running the seed script):</p>
          <p>healthworker@retinascan.demo / Worker@123</p>
          <p>ophthalmologist@retinascan.demo / Doctor@123</p>
        </div>
      </div>
    </div>
  );
}
