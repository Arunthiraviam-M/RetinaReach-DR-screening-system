import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import { ThemeProvider } from './context/ThemeContext';
import { LanguageProvider } from './i18n/LanguageContext';
import { ToastProvider } from './context/ToastContext';
import { AuthProvider } from './context/AuthContext';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 15000 },
  },
});

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <LanguageProvider>
          <ThemeProvider>
            <ToastProvider>
              <AuthProvider>
                <App />
              </AuthProvider>
            </ToastProvider>
          </ThemeProvider>
        </LanguageProvider>
      </QueryClientProvider>
    </BrowserRouter>
  </React.StrictMode>
);
