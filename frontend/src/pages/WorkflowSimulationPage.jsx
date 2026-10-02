import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Camera, Cpu, Users2, Gauge, Wifi, Clock, PlayCircle, Loader2 } from 'lucide-react';
import { simulationApi } from '../api/endpoints';
import { useTranslation } from '../i18n/LanguageContext';

const DEFAULTS = {
  name: 'My Scenario',
  num_cameras: 12,
  images_per_camera_per_day: 35,
  avg_image_size_mb: 3.5,
  uplink_bandwidth_mbps: 5,
  gpu_nodes: 2,
  avg_inference_seconds_per_image: 4,
  ophthalmologists: 3,
  avg_review_seconds_per_case: 25,
  working_hours_per_day: 8,
  target_annual_patients: 100000,
};

function Node({ icon: Icon, label, value, sub, warn }) {
  return (
    <div
      className={`rounded-2xl border p-4 text-center ${
        warn
          ? 'border-rose-300 bg-rose-50 dark:bg-rose-950/30 dark:border-rose-900'
          : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900'
      }`}
    >
      <Icon size={20} className={`mx-auto mb-2 ${warn ? 'text-rose-500' : 'text-brand-500'}`} />
      <p className="text-lg font-bold text-slate-900 dark:text-white leading-none">{value}</p>
      <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">{label}</p>
      {sub && <p className="text-[10px] text-slate-400 mt-0.5">{sub}</p>}
    </div>
  );
}

function Field({ label, value, onChange, step = 1, suffix }) {
  return (
    <div>
      <label className="label text-xs">{label}</label>
      <div className="relative">
        <input
          type="number"
          step={step}
          className="input"
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
        />
        {suffix && <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400">{suffix}</span>}
      </div>
    </div>
  );
}

export default function WorkflowSimulationPage() {
  const { t } = useTranslation();
  const [form, setForm] = useState(DEFAULTS);
  const [result, setResult] = useState(null);

  const mutation = useMutation({
    mutationFn: () => simulationApi.run(form),
    onSuccess: (data) => setResult(data),
  });

  const set = (field) => (val) => setForm((f) => ({ ...f, [field]: val }));

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <p className="text-sm text-slate-500 dark:text-slate-400 max-w-3xl">
        Model the district screening pipeline like a Simulink block diagram — cameras feed the network, the network
        feeds GPU processing nodes, and processed studies queue for ophthalmologist review. Adjust any parameter and
        re-run to see the effect on throughput, bottlenecks, and turnaround time.
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Parameters */}
        <div className="card p-5 space-y-5 lg:col-span-1">
          <h3 className="font-semibold text-slate-900 dark:text-white">Scenario Parameters</h3>

          <div className="space-y-3">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Acquisition</p>
            <Field label="Cameras deployed" value={form.num_cameras} onChange={set('num_cameras')} />
            <Field label="Images / camera / day" value={form.images_per_camera_per_day} onChange={set('images_per_camera_per_day')} />
            <Field label="Avg image size" value={form.avg_image_size_mb} onChange={set('avg_image_size_mb')} step={0.1} suffix="MB" />
          </div>

          <div className="space-y-3">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Network</p>
            <Field label="Uplink bandwidth" value={form.uplink_bandwidth_mbps} onChange={set('uplink_bandwidth_mbps')} step={0.5} suffix="Mbps" />
          </div>

          <div className="space-y-3">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Processing</p>
            <Field label="GPU nodes" value={form.gpu_nodes} onChange={set('gpu_nodes')} />
            <Field label="Inference time / image" value={form.avg_inference_seconds_per_image} onChange={set('avg_inference_seconds_per_image')} step={0.5} suffix="sec" />
          </div>

          <div className="space-y-3">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Review</p>
            <Field label="Ophthalmologists" value={form.ophthalmologists} onChange={set('ophthalmologists')} />
            <Field label="Review time / case" value={form.avg_review_seconds_per_case} onChange={set('avg_review_seconds_per_case')} step={1} suffix="sec" />
            <Field label="Working hours / day" value={form.working_hours_per_day} onChange={set('working_hours_per_day')} step={0.5} />
          </div>

          <Field label="Target patients / year" value={form.target_annual_patients} onChange={set('target_annual_patients')} step={1000} />

          <button onClick={() => mutation.mutate()} disabled={mutation.isPending} className="btn-primary w-full py-2.5">
            {mutation.isPending ? <Loader2 size={16} className="animate-spin" /> : <PlayCircle size={16} />}
            Run Simulation
          </button>
        </div>

        {/* Diagram / results */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6">
            <h3 className="font-semibold text-slate-900 dark:text-white mb-5">Pipeline (Simulink-style)</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <Node icon={Camera} label="Images / day" value={result?.daily_images_generated ?? '—'} />
              <Node
                icon={Wifi}
                label="Bandwidth needed"
                value={result ? `${result.bandwidth_required_mbps} Mbps` : '—'}
                sub={result ? `of ${form.uplink_bandwidth_mbps} Mbps available` : null}
                warn={result?.bandwidth_bottleneck}
              />
              <Node
                icon={Cpu}
                label="Processing capacity"
                value={result?.daily_processing_capacity ?? '—'}
                sub="images / day"
                warn={result?.processing_bottleneck}
              />
              <Node
                icon={Users2}
                label="Review capacity"
                value={result?.daily_review_capacity ?? '—'}
                sub="cases / day"
                warn={result?.review_bottleneck}
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-5">
              <Node icon={Clock} label="Avg turnaround time" value={result ? `${result.avg_turnaround_minutes} min` : '—'} />
              <Node
                icon={Gauge}
                label="Projected annual capacity"
                value={result ? result.annual_capacity.toLocaleString() : '—'}
                sub={result ? (result.meets_target ? '✓ meets target' : '✗ below target') : null}
                warn={result && !result.meets_target}
              />
            </div>
          </div>

          {result && (
            <div className="card p-5">
              <h3 className="font-semibold text-slate-900 dark:text-white mb-3">Interpretation</h3>
              <ul className="text-sm text-slate-600 dark:text-slate-300 space-y-2 list-disc list-inside">
                {result.bandwidth_bottleneck && (
                  <li>Network uplink is the bottleneck — consider image compression or a higher-bandwidth link.</li>
                )}
                {result.processing_bottleneck && (
                  <li>GPU processing can't keep up with acquisition — add GPU nodes or optimize inference time.</li>
                )}
                {result.review_bottleneck && (
                  <li>Ophthalmologist review is the bottleneck — add reviewers or extend working hours.</li>
                )}
                {!result.bandwidth_bottleneck && !result.processing_bottleneck && !result.review_bottleneck && (
                  <li>No bottleneck detected at this configuration — pipeline is balanced end-to-end.</li>
                )}
                <li>
                  At this configuration, the program can screen approximately{' '}
                  <strong>{result.annual_capacity.toLocaleString()}</strong> patients/year against a target of{' '}
                  {form.target_annual_patients.toLocaleString()}.
                </li>
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
