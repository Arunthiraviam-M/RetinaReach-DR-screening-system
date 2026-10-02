import { createContext, useCallback, useContext, useState } from 'react';
import { CheckCircle2, XCircle, Info, X } from 'lucide-react';

const ToastContext = createContext(null);

const ICONS = {
  success: CheckCircle2,
  error: XCircle,
  info: Info,
};

const STYLES = {
  success: 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200 dark:border-emerald-900',
  error: 'border-rose-200 bg-rose-50 text-rose-800 dark:bg-rose-950 dark:text-rose-200 dark:border-rose-900',
  info: 'border-brand-200 bg-brand-50 text-brand-800 dark:bg-brand-950 dark:text-brand-200 dark:border-brand-900',
};

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const dismiss = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const push = useCallback(
    (message, type = 'info') => {
      const id = Date.now() + Math.random();
      setToasts((prev) => [...prev, { id, message, type }]);
      setTimeout(() => dismiss(id), 4500);
    },
    [dismiss]
  );

  const toast = {
    success: (msg) => push(msg, 'success'),
    error: (msg) => push(msg, 'error'),
    info: (msg) => push(msg, 'info'),
  };

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 w-[min(92vw,380px)]">
        {toasts.map((t) => {
          const Icon = ICONS[t.type];
          return (
            <div
              key={t.id}
              className={`fade-in flex items-start gap-2.5 rounded-xl border px-4 py-3 shadow-lg text-sm ${STYLES[t.type]}`}
            >
              <Icon size={18} className="mt-0.5 shrink-0" />
              <p className="flex-1">{t.message}</p>
              <button onClick={() => dismiss(t.id)} className="opacity-60 hover:opacity-100">
                <X size={15} />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}
