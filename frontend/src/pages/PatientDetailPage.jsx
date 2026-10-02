import { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Download, RefreshCcw, Loader2, ImageOff } from 'lucide-react';
import { patientsApi, reportsApi, studiesApi } from '../api/endpoints';
import { mediaUrl } from '../api/client';
import { useToast } from '../context/ToastContext';
import { extractErrorMessage } from '../api/client';
import { useTranslation } from '../i18n/LanguageContext';

function gradeTone(grade, referable) {
  if (grade === undefined || grade === null) return 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400';
  return referable
    ? 'bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300'
    : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300';
}

export default function PatientDetailPage() {
  const { patientId } = useParams();
  const { t } = useTranslation();
  const toast = useToast();
  const navigate = useNavigate();
  const [busyStudyId, setBusyStudyId] = useState(null);
  const [creatingScreening, setCreatingScreening] = useState(false);
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['patient-history', patientId],
    queryFn: () => patientsApi.history(patientId),
  });

  const handleDownload = async (studyId, patientCode) => {
    setBusyStudyId(studyId);
    try {
      await reportsApi.download(studyId, `${patientCode}_report.pdf`);
    } catch (err) {
      toast.error(extractErrorMessage(err, 'Download failed. Generate a report first.'));
    } finally {
      setBusyStudyId(null);
    }
  };

  const handleRegenerate = async (studyId) => {
    setBusyStudyId(studyId);
    try {
      await reportsApi.generate(studyId);
      toast.success('Report regenerated.');
      refetch();
    } catch (err) {
      toast.error(extractErrorMessage(err, 'Could not regenerate report.'));
    } finally {
      setBusyStudyId(null);
    }
  };
    const handleNewScreening = async () => {
    setCreatingScreening(true);

    try {
      const study = await studiesApi.create(patientId);

      toast.success('New screening created.');

      navigate(`/app/study/${study.id}`);
    } catch (err) {
      toast.error(extractErrorMessage(err, 'Could not create a new screening.'));
    } finally {
      setCreatingScreening(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="animate-spin text-brand-500" size={28} />
      </div>
    );
  }

  if (!data) return null;
  const { patient, studies } = data;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Link to="/app/patients" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 dark:hover:text-slate-200">
        <ArrowLeft size={15} /> {t('back')}
      </Link>

      <div className="card p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">{patient.full_name}</h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">{patient.patient_code}</p>
          </div>
          <span className="badge bg-brand-50 text-brand-700 dark:bg-brand-950/50 dark:text-brand-300">
            {patient.district || 'District not set'}
          </span>
        </div>

        <dl className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-5 text-sm">
          <div>
            <dt className="text-slate-400 text-xs">{t('age')} / {t('sex')}</dt>
            <dd className="font-medium text-slate-800 dark:text-slate-100">{patient.age} / {patient.sex}</dd>
          </div>
          <div>
            <dt className="text-slate-400 text-xs">{t('diabetesStatus')}</dt>
            <dd className="font-medium text-slate-800 dark:text-slate-100 capitalize">{patient.diabetes_status.replace('_', ' ')}</dd>
          </div>
          <div>
            <dt className="text-slate-400 text-xs">{t('hba1c')}</dt>
            <dd className="font-medium text-slate-800 dark:text-slate-100">{patient.hba1c ?? '—'}</dd>
          </div>
          <div>
            <dt className="text-slate-400 text-xs">{t('village')}</dt>
            <dd className="font-medium text-slate-800 dark:text-slate-100">{patient.village || '—'}</dd>
          </div>
        </dl>
      </div>

            <div>
        <div className="flex items-center justify-between gap-3 mb-3">
          <h3 className="font-semibold text-slate-900 dark:text-white">
            {t('patientHistory')} (A–Z)
          </h3>

          <button
            onClick={handleNewScreening}
            disabled={creatingScreening}
            className="btn-primary text-sm px-4 py-2"
          >
            {creatingScreening ? (
              <Loader2 size={15} className="animate-spin" />
            ) : (
              '+'
            )}
            {creatingScreening ? 'Creating...' : 'New Screening'}
          </button>
        </div>
        <div className="space-y-3">
          {!studies.length && (
            <div className="card p-8 text-center text-slate-400 text-sm">No studies recorded yet.</div>
          )}
          {studies.map((study) => {
            const grading = study.grading_result;
            const fundusImg = study.images.find((i) => i.modality === 'fundus') || study.images[0];
            return (
              <div key={study.id} className="card p-4 flex flex-wrap items-center gap-4">
                <div className="h-16 w-20 rounded-lg overflow-hidden bg-black shrink-0 flex items-center justify-center">
                  {fundusImg ? (
                    <img
                      src={mediaUrl(fundusImg.enhanced_url || fundusImg.original_url)}
                      alt="fundus"
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <ImageOff size={18} className="text-slate-600" />
                  )}
                </div>

                <div className="flex-1 min-w-[160px]">
                  <p className="text-sm font-medium text-slate-800 dark:text-slate-100">
                    {new Date(study.created_at).toLocaleDateString(undefined, {
                      day: '2-digit',
                      month: 'short',
                      year: 'numeric',
                    })}
                  </p>
                  <span className={`badge mt-1 ${gradeTone(grading?.dr_grade, grading?.referable_dr)}`}>
                    {grading ? `Level ${grading.dr_grade} — ${grading.dr_grade_label}` : study.status.replace('_', ' ')}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <Link to={`/app/study/${study.id}`} className="btn-ghost text-sm">
                    {t('view')}
                  </Link>
                  {grading && (
                    <>
                      <button
                        onClick={() => handleDownload(study.id, patient.patient_code)}
                        disabled={busyStudyId === study.id}
                        className="btn-secondary text-sm px-3 py-2"
                      >
                        <Download size={14} /> PDF
                      </button>
                      <button
                        onClick={() => handleRegenerate(study.id)}
                        disabled={busyStudyId === study.id}
                        className="btn-ghost text-sm px-2"
                        title={t('regenerateReport')}
                      >
                        <RefreshCcw size={15} />
                      </button>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
