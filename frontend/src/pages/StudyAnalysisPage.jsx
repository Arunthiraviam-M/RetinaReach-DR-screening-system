import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  AlertCircle,
  ArrowLeft,
  FileText,
  Loader2,
  CheckCircle2,
  XCircle,
  Info,
} from 'lucide-react';
import { studiesApi, reportsApi } from '../api/endpoints';
import { mediaUrl } from '../api/client';
import ImageUploadCard from '../components/ImageUploadCard';
import { useToast } from '../context/ToastContext';
import { extractErrorMessage } from '../api/client';
import { useTranslation } from '../i18n/LanguageContext';

const GRADE_STYLES = {
  0: { color: 'emerald', label: 'No DR' },
  1: { color: 'lime', label: 'Mild NPDR' },
  2: { color: 'amber', label: 'Moderate NPDR' },
  3: { color: 'orange', label: 'Severe NPDR' },
  4: { color: 'rose', label: 'Proliferative DR' },
};

const COLOR_CLASSES = {
  emerald: 'bg-emerald-50 border-emerald-200 text-emerald-800 dark:bg-emerald-950/40 dark:border-emerald-900 dark:text-emerald-300',
  lime: 'bg-lime-50 border-lime-200 text-lime-800 dark:bg-lime-950/40 dark:border-lime-900 dark:text-lime-300',
  amber: 'bg-amber-50 border-amber-200 text-amber-800 dark:bg-amber-950/40 dark:border-amber-900 dark:text-amber-300',
  orange: 'bg-orange-50 border-orange-200 text-orange-800 dark:bg-orange-950/40 dark:border-orange-900 dark:text-orange-300',
  rose: 'bg-rose-50 border-rose-200 text-rose-800 dark:bg-rose-950/40 dark:border-rose-900 dark:text-rose-300',
};

const LESION_LABELS = {
  microaneurysm: 'Microaneurysms',
  hemorrhage: 'Hemorrhages',
  hard_exudate: 'Exudates',
  neovascularization: 'Neovascularization',
};

function DisplayImage({ src, label }) {
  if (!src) return null;
  return (
    <div>
      <div
        className="rounded-xl overflow-hidden bg-black border border-slate-200 dark:border-slate-800"
        style={{ width: '100%', aspectRatio: '400 / 300' }}
      >
        <img src={src} alt={label} className="h-full w-full object-contain" width={400} height={300} />
      </div>
      <p className="text-center text-xs font-medium text-slate-500 dark:text-slate-400 mt-2">{label}</p>
    </div>
  );
}

export default function StudyAnalysisPage() {
  const { studyId } = useParams();
  const { t } = useTranslation();
  const toast = useToast();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [generating, setGenerating] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  const { data: study, isLoading } = useQuery({
    queryKey: ['study', studyId],
    queryFn: () => studiesApi.get(studyId),
  });

  const handleAnalyze = async () => {
    setAnalyzing(true);

    try {
      await studiesApi.analyze(studyId);
      await queryClient.invalidateQueries({ queryKey: ['study', studyId] });
      toast.success('New images analyzed successfully.');
    } catch (err) {
      toast.error(extractErrorMessage(err, 'Could not analyze the new images.'));
      await queryClient.invalidateQueries({ queryKey: ['study', studyId] });
    } finally {
      setAnalyzing(false);
    }
  };

  const handleGenerateReport = async () => {
    setGenerating(true);
    try {
      await reportsApi.generate(studyId);
      navigate(`/app/study/${studyId}/report`);
    } catch (err) {
      toast.error(extractErrorMessage(err, 'Could not generate report.'));
    } finally {
      setGenerating(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="animate-spin text-brand-500" size={28} />
      </div>
    );
  }

  if (!study) return null;

  const studyStatus = String(study.status || '').toLowerCase();
  const isAnalyzed = studyStatus === 'analyzed';

  // Only show a grading result when it belongs to the current
  // analyzed version of this study.
  const grading = isAnalyzed ? study.grading_result : null;

  const primaryImage =
    study.images.find((img) => img.modality === 'fundus') || study.images[0];

  const gradeMeta = grading ? GRADE_STYLES[grading.dr_grade] : null;

  const getAsset = (modality, laterality) =>
    study.images.find(
      (img) =>
        img.modality === modality &&
        (img.laterality || null) === (laterality || null)
    );

  const handleUploaded = async () => {
    // Upload only performs quality checking.
    // Analysis is intentionally started by the Analyze button.
    await queryClient.invalidateQueries({ queryKey: ['study', studyId] });
  };

  const hasGradeableFundus = study.images.some(
    (img) =>
      img.modality === 'fundus' &&
      img.quality &&
      img.quality.verdict !== 'ungradeable'
  );

  const showAnalyzeButton = !isAnalyzed && hasGradeableFundus;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <button
        onClick={() => navigate(-1)}
        className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
      >
        <ArrowLeft size={15} /> {t('back')}
      </button>

      <div className="card p-5 flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="font-bold text-lg text-slate-900 dark:text-white">
            {t('detailedAnalysis')}
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Study #{study.patient_code}
          </p>
        </div>

        {grading && gradeMeta && (
          <span
            className={`badge border text-sm px-3 py-1.5 ${COLOR_CLASSES[gradeMeta.color]}`}
          >
            Level {grading.dr_grade} — {gradeMeta.label}
          </span>
        )}
      </div>

      <div className="mb-6">
        <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-3">
          Screening Images
        </h2>

        <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
          Re-upload or retake only the image that needs correction. Other images in this screening remain unchanged.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ImageUploadCard
            studyId={studyId}
            modality="fundus"
            laterality="right"
            label="Fundus — Right Eye"
            existingAsset={getAsset('fundus', 'right')}
            onUploaded={handleUploaded}
          />

          <ImageUploadCard
            studyId={studyId}
            modality="fundus"
            laterality="left"
            label="Fundus — Left Eye"
            existingAsset={getAsset('fundus', 'left')}
            onUploaded={handleUploaded}
          />

          <ImageUploadCard
            studyId={studyId}
            modality="oct"
            laterality="right"
            label="OCT — Right Eye"
            existingAsset={getAsset('oct', 'right')}
            onUploaded={handleUploaded}
          />

          <ImageUploadCard
            studyId={studyId}
            modality="oct"
            laterality="left"
            label="OCT — Left Eye"
            existingAsset={getAsset('oct', 'left')}
            onUploaded={handleUploaded}
          />
        </div>
      </div>

      {showAnalyzeButton && (
        <div className="card p-5">
          <button
            type="button"
            onClick={handleAnalyze}
            disabled={analyzing}
            className="btn-primary w-full py-3"
          >
            {analyzing ? (
              <Loader2 size={18} className="animate-spin" />
            ) : (
              <CheckCircle2 size={18} />
            )}
            {analyzing ? 'Analyzing New Images...' : 'Analyze New Images'}
          </button>

          <p className="text-xs text-slate-400 text-center mt-2">
            The AI analysis will use the current uploaded Fundus image(s) for this screening.
          </p>
        </div>
      )}

      {!grading ? (
        <div className="card p-10 text-center text-slate-400">
          <AlertCircle className="mx-auto mb-3" size={28} />

          {hasGradeableFundus
            ? 'This screening has not been analyzed yet. Click "Analyze New Images" to continue.'
            : 'Upload at least one gradeable Fundus image before analysis.'}
        </div>
      ) : (
        <>
          {/* Plain-language summary banner */}
          <div className={`rounded-2xl border p-5 ${COLOR_CLASSES[gradeMeta.color]}`}>
            <p className="font-semibold text-base mb-1">
              {grading.rationale_summary}
            </p>
            <p className="text-sm opacity-90 leading-relaxed">
              {grading.rationale_detailed}
            </p>
          </div>

          {/* Images row */}
          <div className="card p-5">
            <h3 className="font-semibold text-slate-900 dark:text-white mb-4">
              {t('gradCamExplanation')}
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <DisplayImage
                src={mediaUrl(primaryImage?.original_url)}
                label={t('originalImage')}
              />

              {primaryImage?.enhanced_url && (
                <DisplayImage
                  src={mediaUrl(primaryImage?.enhanced_url)}
                  label={t('enhancedImage')}
                />
              )}

              <DisplayImage
                src={mediaUrl(primaryImage?.gradcam_url)}
                label={t('gradCamHeatmap')}
              />
            </div>

            <p className="text-xs text-slate-400 mt-4 leading-relaxed">
              The highlighted (red/yellow) regions show where the analysis found the strongest evidence for its
              grading decision — typically clusters of microaneurysms, hemorrhages, or exudates. Blue/green areas
              contributed little to the decision.
            </p>
          </div>

          {/* AI Analysis Summary + confidence */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="card p-5 lg:col-span-2">
              <h3 className="font-semibold text-slate-900 dark:text-white mb-4">
                {t('aiAnalysisSummary')}
              </h3>

              <dl className="space-y-3 text-sm">
                <div className="flex justify-between border-b border-slate-100 dark:border-slate-800 pb-2.5">
                  <dt className="text-slate-500 dark:text-slate-400">
                    {t('drSeverity')}
                  </dt>
                  <dd className="font-semibold text-slate-800 dark:text-slate-100">
                    Level {grading.dr_grade} — {grading.dr_grade_label}
                  </dd>
                </div>

                <div className="flex justify-between border-b border-slate-100 dark:border-slate-800 pb-2.5">
                  <dt className="text-slate-500 dark:text-slate-400">
                    {t('referableDR')}
                  </dt>
                  <dd
                    className={`font-semibold flex items-center gap-1 ${
                      grading.referable_dr
                        ? 'text-rose-600'
                        : 'text-emerald-600'
                    }`}
                  >
                    {grading.referable_dr ? (
                      <XCircle size={15} />
                    ) : (
                      <CheckCircle2 size={15} />
                    )}
                    {grading.referable_dr ? t('yes') : t('no')}
                  </dd>
                </div>

                <div className="flex justify-between">
                  <dt className="text-slate-500 dark:text-slate-400">
                    {t('confidenceScore')}
                  </dt>
                  <dd className="font-semibold text-slate-800 dark:text-slate-100">
                    {Math.round(grading.confidence * 100)}%
                  </dd>
                </div>
              </dl>

              <h4 className="font-semibold text-slate-900 dark:text-white mt-6 mb-3">
                {t('findings')}
              </h4>

              <ul className="space-y-2">
                {grading.lesions.map((lesion) => (
                  <li
                    key={lesion.lesion_type}
                    className="flex items-start gap-2.5 text-sm"
                  >
                    {lesion.detected ? (
                      <CheckCircle2
                        size={16}
                        className="text-amber-500 mt-0.5 shrink-0"
                      />
                    ) : (
                      <XCircle
                        size={16}
                        className="text-slate-300 dark:text-slate-600 mt-0.5 shrink-0"
                      />
                    )}

                    <div>
                      <p className="font-medium text-slate-800 dark:text-slate-100">
                        {LESION_LABELS[lesion.lesion_type] || lesion.lesion_type}{' '}
                        {lesion.detected ? (
                          <span className="text-amber-600 font-normal">
                            ({t('detected')}
                            {lesion.count_estimate
                              ? ` × ${lesion.count_estimate}`
                              : ''}
                            )
                          </span>
                        ) : (
                          <span className="text-slate-400 font-normal">
                            ({t('notDetected')})
                          </span>
                        )}
                      </p>

                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        {lesion.description}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            <div className="card p-5">
              <h3 className="font-semibold text-slate-900 dark:text-white mb-3 flex items-center gap-1.5">
                <Info size={16} className="text-brand-500" /> {t('recommendation')}
              </h3>

              <p className="font-bold text-slate-900 dark:text-white mb-2">
                {grading.recommendation}
              </p>

              <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1">
                {t('whyThisMatters')}
              </p>

              <p className="text-sm text-slate-600 dark:text-slate-300 mb-4">
                {grading.recommendation_reason}
              </p>

              <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1">
                {t('whoCanRefer')}
              </p>

              <p className="text-sm text-slate-600 dark:text-slate-300">
                {grading.refer_to}
              </p>

              <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800">
                <p className="text-[10px] text-slate-400">
                  Model: {grading.model_version}
                </p>
              </div>
            </div>
          </div>

          <button
            onClick={handleGenerateReport}
            disabled={generating}
            className="btn-primary w-full py-3"
          >
            {generating ? (
              <Loader2 size={18} className="animate-spin" />
            ) : (
              <FileText size={18} />
            )}
            {t('generateReport')}
          </button>
        </>
      )}
    </div>
  );
}