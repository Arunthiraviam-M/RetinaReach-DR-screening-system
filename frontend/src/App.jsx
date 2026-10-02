import { Navigate, Route, Routes } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import AppLayout from './layouts/AppLayout';
import DashboardPage from './pages/DashboardPage';
import NewRegistrationPage from './pages/NewRegistrationPage';
import StudyAnalysisPage from './pages/StudyAnalysisPage';
import StudyReportPage from './pages/StudyReportPage';
import PatientDatabasePage from './pages/PatientDatabasePage';
import PatientDetailPage from './pages/PatientDetailPage';
import WorkflowSimulationPage from './pages/WorkflowSimulationPage';
import ReportsOverviewPage from './pages/ReportsOverviewPage';

function ProtectedRoute({ children }) {
  const { user, initializing } = useAuth();
  if (initializing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="h-8 w-8 rounded-full border-2 border-brand-500 border-t-transparent animate-spin" />
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function PublicOnlyRoute({ children }) {
  const { user, initializing } = useAuth();
  if (initializing) return null;
  if (user) return <Navigate to="/app/dashboard" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route
        path="/login"
        element={
          <PublicOnlyRoute>
            <LoginPage />
          </PublicOnlyRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicOnlyRoute>
            <RegisterPage />
          </PublicOnlyRoute>
        }
      />

      <Route
        path="/app"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="registration" element={<NewRegistrationPage />} />
        <Route path="study/:studyId" element={<StudyAnalysisPage />} />
        <Route path="study/:studyId/report" element={<StudyReportPage />} />
        <Route path="patients" element={<PatientDatabasePage />} />
        <Route path="patients/:patientId" element={<PatientDetailPage />} />
        <Route path="simulation" element={<WorkflowSimulationPage />} />
        <Route path="reports" element={<ReportsOverviewPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
