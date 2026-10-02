import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Loader2, CheckCircle2 } from 'lucide-react';
import { patientsApi, studiesApi } from '../api/endpoints';
import { useToast } from '../context/ToastContext';
import { extractErrorMessage } from '../api/client';
import { useTranslation } from '../i18n/LanguageContext';
import ImageUploadCard from '../components/ImageUploadCard';

const STEPS = ['patientDetails', 'uploadImages', 'continueToAnalysis'];

export default function NewRegistrationPage() {
  const { t } = useTranslation();
  const toast = useToast();
  const navigate = useNavigate();

  const [step, setStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [patient, setPatient] = useState(null);
  const [study, setStudy] = useState(null);

  const [form, setForm] = useState({
    full_name: '',
    age: '',
    sex: 'male',
    phone: '',
    village: '',
    district: '',
    state: 'Tamil Nadu',
    diabetes_status: 'unknown',
    diabetes_duration_years: '',
    hba1c: '',
    other_conditions: '',
  });

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleCreatePatient = async (e) => {
    e.preventDefault();
    if (!form.full_name || !form.age) {
      toast.error('Name and age are required.');
      return;
    }
    setSaving(true);
    try {
      const payload = {
        ...form,
        age: Number(form.age),
        diabetes_duration_years: form.diabetes_duration_years ? Number(form.diabetes_duration_years) : null,
        hba1c: form.hba1c ? Number(form.hba1c) : null,
      };
      const createdPatient = await patientsApi.create(payload);
      const createdStudy = await studiesApi.create(createdPatient.id);
      setPatient(createdPatient);
      setStudy(createdStudy);
      setStep(1);
      toast.success(`Patient registered: ${createdPatient.patient_code}`);
    } catch (err) {
      toast.error(extractErrorMessage(err, 'Could not register patient.'));
    } finally {
      setSaving(false);
    }
  };

  const handleStudyUpdate = (updatedStudy) => setStudy(updatedStudy);

  const gradeableFundusUploaded = study?.images?.some(
    (img) => img.modality === 'fundus' && img.quality?.verdict !== 'ungradeable'
  );

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const analyzed = await studiesApi.analyze(study.id);
      toast.success('Analysis complete.');
      navigate(`/app/study/${analyzed.id}`);
    } catch (err) {
      toast.error(extractErrorMessage(err, 'Analysis failed.'));
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Stepper */}
      <div className="flex items-center gap-2">
        {STEPS.map((s, i) => (
          <div key={s} className="flex items-center flex-1">
            <div
              className={`h-8 w-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                i < step
                  ? 'bg-emerald-500 text-white'
                  : i === step
                  ? 'bg-brand-600 text-white'
                  : 'bg-slate-200 dark:bg-slate-800 text-slate-500'
              }`}
            >
              {i < step ? <CheckCircle2 size={16} /> : i + 1}
            </div>
            {i < STEPS.length - 1 && (
              <div className={`h-0.5 flex-1 mx-2 ${i < step ? 'bg-emerald-500' : 'bg-slate-200 dark:bg-slate-800'}`} />
            )}
          </div>
        ))}
      </div>

      {step === 0 && (
        <form onSubmit={handleCreatePatient} className="card p-6 space-y-5">
          <h2 className="font-semibold text-lg text-slate-900 dark:text-white">{t('patientDetails')}</h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="sm:col-span-2">
              <label className="label">{t('fullName')} *</label>
              <input className="input" value={form.full_name} onChange={update('full_name')} required />
            </div>
            <div>
              <label className="label">{t('age')} *</label>
              <input type="number" min="0" max="120" className="input" value={form.age} onChange={update('age')} required />
            </div>
            <div>
              <label className="label">{t('sex')} *</label>
              <select className="input" value={form.sex} onChange={update('sex')}>
                <option value="male">{t('male')}</option>
                <option value="female">{t('female')}</option>
                <option value="other">{t('other')}</option>
              </select>
            </div>
            <div>
              <label className="label">{t('phone')}</label>
              <input className="input" value={form.phone} onChange={update('phone')} />
            </div>
            <div>
              <label className="label">{t('village')}</label>
              <input className="input" value={form.village} onChange={update('village')} />
            </div>
            <div>
              <label className="label">{t('district')}</label>
              <input className="input" value={form.district} onChange={update('district')} />
            </div>
            <div>
              <label className="label">State</label>
              <input className="input" value={form.state} onChange={update('state')} />
            </div>
          </div>

          <div className="border-t border-slate-100 dark:border-slate-800 pt-5">
            <p className="label mb-3">{t('diabetesStatus')}</p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {[
                { value: 'known', label: t('diabetesKnown') },
                { value: 'unknown', label: t('diabetesUnknown') },
                { value: 'not_diabetic', label: t('notDiabetic') },
              ].map((opt) => (
                <label
                  key={opt.value}
                  className={`flex items-center gap-2 rounded-xl border px-3 py-2.5 cursor-pointer text-sm ${
                    form.diabetes_status === opt.value
                      ? 'border-brand-500 bg-brand-50 dark:bg-brand-950/40 text-brand-700 dark:text-brand-300'
                      : 'border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400'
                  }`}
                >
                  <input
                    type="radio"
                    name="diabetes_status"
                    className="hidden"
                    checked={form.diabetes_status === opt.value}
                    onChange={() => setForm((f) => ({ ...f, diabetes_status: opt.value }))}
                  />
                  {opt.label}
                </label>
              ))}
            </div>

            {form.diabetes_status === 'known' && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
                <div>
                  <label className="label">{t('diabetesDuration')}</label>
                  <input
                    type="number"
                    step="0.5"
                    className="input"
                    value={form.diabetes_duration_years}
                    onChange={update('diabetes_duration_years')}
                  />
                </div>
                <div>
                  <label className="label">{t('hba1c')}</label>
                  <input type="number" step="0.1" className="input" value={form.hba1c} onChange={update('hba1c')} />
                </div>
              </div>
            )}

            <div className="mt-4">
              <label className="label">Other conditions (optional)</label>
              <input
                className="input"
                placeholder="e.g. hypertension, prior eye surgery"
                value={form.other_conditions}
                onChange={update('other_conditions')}
              />
            </div>
          </div>

          <button type="submit" disabled={saving} className="btn-primary w-full py-3">
            {saving ? <Loader2 size={18} className="animate-spin" /> : <ArrowRight size={18} />}
            {t('next')}
          </button>
        </form>
      )}

      {step === 1 && study && (
        <div className="space-y-6">
          <div className="card p-5 flex items-center justify-between">
            <div>
              <p className="font-semibold text-slate-900 dark:text-white">{patient.full_name}</p>
              <p className="text-sm text-slate-500 dark:text-slate-400">{patient.patient_code}</p>
            </div>
            <span className="badge bg-brand-50 text-brand-700 dark:bg-brand-950/50 dark:text-brand-300">
              {t('uploadImages')}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <ImageUploadCard
              studyId={study.id}
              modality="fundus"
              laterality="right"
              label={`${t('fundusImage')} — ${t('rightEye')}`}
              onUploaded={handleStudyUpdate}
            />
            <ImageUploadCard
              studyId={study.id}
              modality="fundus"
              laterality="left"
              label={`${t('fundusImage')} — ${t('leftEye')}`}
              onUploaded={handleStudyUpdate}
            />
            <ImageUploadCard
              studyId={study.id}
              modality="oct"
              laterality="right"
              label={`${t('octImage')} — ${t('rightEye')}`}
              onUploaded={handleStudyUpdate}
            />
            <ImageUploadCard
              studyId={study.id}
              modality="oct"
              laterality="left"
              label={`${t('octImage')} — ${t('leftEye')}`}
              onUploaded={handleStudyUpdate}
            />
          </div>

          <button
            onClick={handleAnalyze}
            disabled={!gradeableFundusUploaded || analyzing}
            className="btn-primary w-full py-3"
          >
            {analyzing ? <Loader2 size={18} className="animate-spin" /> : <ArrowRight size={18} />}
            {t('continueToAnalysis')}
          </button>
          {!gradeableFundusUploaded && (
            <p className="text-center text-xs text-slate-400">
              Upload at least one gradeable fundus image (right or left eye) to continue.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
