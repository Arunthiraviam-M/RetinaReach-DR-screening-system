import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Download, RefreshCcw, Loader2, FileCheck2, ArrowLeft } from 'lucide-react';
import { reportsApi, studiesApi } from '../api/endpoints';
import { useToast } from '../context/ToastContext';
import { extractErrorMessage } from '../api/client';
import { useTranslation } from '../i18n/LanguageContext';

export default function StudyReportPage() {
  const { studyId } = useParams();
  const { t } = useTranslation();
  const toast = useToast();
  const navigate = useNavigate();
  const [downloading, setDownloading] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  const { data: study } = useQuery({ queryKey: ['study', studyId], queryFn: () => studiesApi.get(studyId) });
  const {
    data: report,
    refetch,
    isLoading,
  } = useQuery({
    queryKey: ['report', studyId],
    queryFn: () => reportsApi.getLatest(studyId),
    retry: false,
  });

  const handleDownload = async () => {
    setDownloading(true);
    try {
      await reportsApi.download(studyId, `${study?.patient_code || 'patient'}_report.pdf`);
    } catch (err) {
      toast.error(extractErrorMessage(err, 'Download failed.'));
    } finally {
      setDownloading(false);
    }
  };

  const handleRegenerate = async () => {
    setRegenerating(true);
    try {
      await reportsApi.generate(studyId);
      await refetch();
      toast.success('Report regenerated.');
    } catch (err) {
      toast.error(extractErrorMessage(err, 'Could not regenerate report.'));
    } finally {
      setRegenerating(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <button
        onClick={() => navigate(`/app/study/${studyId}`)}
        className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
      >
        <ArrowLeft size={15} /> {t('back')}
      </button>

      <div className="card p-8 text-center">
        <div className="h-16 w-16 rounded-2xl bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 flex items-center justify-center mx-auto mb-5">
          <FileCheck2 size={30} />
        </div>
        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-1">{t('finalReport')}</h2>

        {isLoading ? (
          <p className="text-slate-400 text-sm mt-4">{t('loading')}</p>
        ) : report ? (
          <>
            <p className="text-slate-500 dark:text-slate-400 text-sm mb-6">
              Patient {report.patient_code} · Level {report.dr_grade} · {Math.round(report.confidence * 100)}%
              confidence · Generated {new Date(report.created_at).toLocaleString()}
            </p>

            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button onClick={handleDownload} disabled={downloading} className="btn-primary px-6 py-3">
                {downloading ? <Loader2 size={18} className="animate-spin" /> : <Download size={18} />}
                {t('downloadPDF')}
              </button>
              <button onClick={handleRegenerate} disabled={regenerating} className="btn-secondary px-6 py-3">
                {regenerating ? <Loader2 size={18} className="animate-spin" /> : <RefreshCcw size={18} />}
                {t('regenerateReport')}
              </button>
            </div>
          </>
        ) : (
          <p className="text-slate-400 text-sm mt-4">{t('noReportsYet')}</p>
        )}

        <Link
          to={`/app/patients/${study?.patient_id}`}
          className="block mt-8 text-sm text-brand-600 font-medium hover:underline"
        >
          View full patient history →
        </Link>
      </div>
    </div>
  );
}
