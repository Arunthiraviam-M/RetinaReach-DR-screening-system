import { useEffect, useRef, useState } from 'react';
import { UploadCloud, CheckCircle2, AlertTriangle, RefreshCcw, Loader2 } from 'lucide-react';
import { studiesApi } from '../api/endpoints';
import { mediaUrl } from '../api/client';
import { useToast } from '../context/ToastContext';
import { useTranslation } from '../i18n/LanguageContext';

const DISPLAY_SIZE = { width: 400, height: 300 };

export default function ImageUploadCard({ studyId, modality, laterality, label, onUploaded, existingAsset }) {
  const { t } = useTranslation();
  const toast = useToast();
  const inputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [asset, setAsset] = useState(existingAsset || null);
  useEffect(() => {
  setAsset(existingAsset || null);
}, [existingAsset]);

  const handleFile = async (file) => {
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      toast.error('Please upload an image file (JPEG/PNG).');
      return;
    }
    setUploading(true);
    setProgress(0);
    try {
      const study = await studiesApi.upload(studyId, modality, laterality, file, setProgress);
      const uploadedAsset = study.images.find(
    (img) =>
    img.modality === modality &&
    (img.laterality || null) === (laterality || null)
);
      setAsset(uploadedAsset);
      onUploaded?.(study);

      if (uploadedAsset.quality?.verdict === 'ungradeable') {
        toast.error('Image quality too low — please recapture per the instructions shown.');
      } else if (uploadedAsset.quality?.verdict === 'borderline_enhanced') {
        toast.success('Image enhanced automatically for grading.');
      } else {
        toast.success('Image quality good.');
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const verdict = asset?.quality?.verdict;

  return (
    <div className="card p-4">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">{label}</p>
        {verdict && (
          <span
            className={`badge ${
              verdict === 'good'
                ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300'
                : verdict === 'borderline_enhanced'
                ? 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300'
                : 'bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300'
            }`}
          >
            {verdict === 'good' && <CheckCircle2 size={12} />}
            {verdict === 'borderline_enhanced' && <RefreshCcw size={12} />}
            {verdict === 'ungradeable' && <AlertTriangle size={12} />}
            {verdict === 'good' ? t('imageQualityGood') : verdict === 'borderline_enhanced' ? t('imageQualityEnhanced') : t('imageUngradeable')}
          </span>
        )}
      </div>

      <div
        onClick={() => !uploading && inputRef.current?.click()}
        style={{ aspectRatio: `${DISPLAY_SIZE.width} / ${DISPLAY_SIZE.height}` }}
        className="relative rounded-xl border-2 border-dashed border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 flex items-center justify-center cursor-pointer overflow-hidden hover:border-brand-400 transition group"
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />

        {uploading ? (
          <div className="flex flex-col items-center gap-2 text-slate-500">
            <Loader2 size={26} className="animate-spin text-brand-500" />
            <p className="text-xs">{progress < 100 ? `Uploading ${progress}%` : t('checkingQuality')}</p>
          </div>
        ) : asset ? (
          <img
            src={mediaUrl(asset.enhanced_url || asset.original_url)}
            alt={label}
            className="h-full w-full object-contain bg-black"
            width={DISPLAY_SIZE.width}
            height={DISPLAY_SIZE.height}
          />
        ) : (
          <div className="flex flex-col items-center gap-2 text-slate-400 group-hover:text-brand-500 transition px-4 text-center">
            <UploadCloud size={28} />
            <p className="text-xs">{t('dragDropImage')}</p>
            <p className="text-[10px] text-slate-400">400 × 300 px display · JPEG/PNG · max 15MB</p>
          </div>
        )}
      </div>

      {asset?.quality && (
        <div className="mt-3 space-y-2">
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="rounded-lg bg-slate-50 dark:bg-slate-800/60 py-1.5">
              <p className="text-[10px] text-slate-400">Sharpness</p>
              <p className="text-xs font-semibold text-slate-700 dark:text-slate-200">{asset.quality.sharpness_score}</p>
            </div>
            <div className="rounded-lg bg-slate-50 dark:bg-slate-800/60 py-1.5">
              <p className="text-[10px] text-slate-400">Illumination</p>
              <p className="text-xs font-semibold text-slate-700 dark:text-slate-200">{asset.quality.illumination_score}</p>
            </div>
            <div className="rounded-lg bg-slate-50 dark:bg-slate-800/60 py-1.5">
              <p className="text-[10px] text-slate-400">Noise</p>
              <p className="text-xs font-semibold text-slate-700 dark:text-slate-200">{asset.quality.noise_score}</p>
            </div>
          </div>

          {asset.quality.enhancement_applied?.length > 0 && (
            <p className="text-[11px] text-amber-700 dark:text-amber-400">
              Auto-enhanced: {asset.quality.enhancement_applied.join(' · ')}
            </p>
          )}

          {verdict === 'ungradeable' && (
            <div className="rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-100 dark:border-rose-900 p-3">
              <p className="text-xs font-semibold text-rose-700 dark:text-rose-300 mb-1">Please recapture:</p>
              <ul className="text-[11px] text-rose-600 dark:text-rose-400 list-disc list-inside space-y-0.5">
                {asset.quality.recapture_instructions.map((instr, i) => (
                  <li key={i}>{instr}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
            {asset && (
        <button
          type="button"
          onClick={() => !uploading && inputRef.current?.click()}
          disabled={uploading}
          className="btn-secondary w-full mt-3 text-sm py-2"
        >
          <RefreshCcw size={14} />
          {asset.quality?.verdict === 'ungradeable'
            ? 'Retake Image'
            : 'Re-upload / Retake'}
        </button>
      )}
    </div>
  );
}
