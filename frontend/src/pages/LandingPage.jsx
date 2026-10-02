import { Link } from 'react-router-dom';
import { Eye, Activity, ShieldCheck, Gauge, ArrowRight } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-white overflow-hidden relative">
      {/* Animated gradient "video" background */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -left-40 h-[36rem] w-[36rem] rounded-full bg-brand-600/30 blur-3xl animate-pulse" />
        <div
          className="absolute -bottom-32 -right-32 h-[30rem] w-[30rem] rounded-full bg-emerald-500/20 blur-3xl animate-pulse"
          style={{ animationDelay: '1.2s' }}
        />
        <div
          className="absolute top-1/3 right-1/4 h-72 w-72 rounded-full bg-indigo-500/20 blur-3xl animate-pulse"
          style={{ animationDelay: '2.4s' }}
        />
        <svg className="absolute inset-0 h-full w-full opacity-[0.07]" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="grid" width="42" height="42" patternUnits="userSpaceOnUse">
              <path d="M 42 0 L 0 0 0 42" fill="none" stroke="white" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>

      {/* Simulated "scanning" retina animation, standing in for the uploaded video */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[560px] w-[560px] opacity-20 pointer-events-none">
        <div className="relative h-full w-full rounded-full border border-brand-400/40">
          <div className="absolute inset-6 rounded-full border border-brand-400/30" />
          <div className="absolute inset-16 rounded-full border border-brand-400/20" />
          <div
            className="absolute inset-0 rounded-full border-t-2 border-brand-400 animate-spin"
            style={{ animationDuration: '6s' }}
          />
        </div>
      </div>

      <div className="relative z-10 flex flex-col min-h-screen">
        <header className="flex items-center justify-between px-6 sm:px-10 py-6">
          <div className="flex items-center gap-2.5">
            <div className="h-9 w-9 rounded-xl bg-brand-500 flex items-center justify-center shadow-lg shadow-brand-500/30">
              <Eye size={20} className="text-white" />
            </div>
            <span className="text-lg font-bold tracking-tight">RetinaScan</span>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/login" className="text-sm font-medium text-slate-300 hover:text-white transition">
              Sign In
            </Link>
            <Link
              to="/register"
              className="btn bg-white text-slate-900 hover:bg-slate-100 px-4 py-2 text-sm font-semibold"
            >
              Register
            </Link>
          </div>
        </header>

        <main className="flex-1 flex flex-col items-center justify-center text-center px-6 py-16">
          <span className="badge bg-brand-500/15 text-brand-300 border border-brand-500/30 mb-6">
            <Activity size={13} /> Explainable AI · Built for Rural Screening Programs
          </span>
          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight max-w-4xl leading-[1.1]">
            Diabetic Retinopathy Screening,{' '}
            <span className="bg-gradient-to-r from-brand-400 to-emerald-400 bg-clip-text text-transparent">
              brought to every village.
            </span>
          </h1>
          <p className="mt-6 max-w-2xl text-slate-300 text-base sm:text-lg leading-relaxed">
            Upload a fundus or OCT image at the primary health centre and get an instant,
            explainable severity grade, lesion-level evidence, and a clinician-ready report —
            built for health workers screening 100,000+ patients a year.
          </p>
          <div className="mt-9 flex flex-col sm:flex-row items-center gap-4">
            <Link to="/register" className="btn-primary px-7 py-3.5 text-base font-semibold">
              Get Started <ArrowRight size={18} />
            </Link>
            <Link
              to="/login"
              className="btn bg-white/5 border border-white/15 text-white hover:bg-white/10 px-7 py-3.5 text-base"
            >
              I already have an account
            </Link>
          </div>

          <div className="mt-20 grid grid-cols-1 sm:grid-cols-3 gap-6 max-w-4xl w-full">
            {[
              {
                icon: Gauge,
                title: 'Under 2-Minute Workflow',
                desc: 'Upload → auto quality-check & enhance → grade → report, built for busy field clinics.',
              },
              {
                icon: Eye,
                title: 'Explainable, Not a Black Box',
                desc: 'Grad-CAM heatmaps and lesion evidence show exactly why a grade was given.',
              },
              {
                icon: ShieldCheck,
                title: 'District-Scale Ready',
                desc: 'Workflow simulation plans camera, GPU, and reviewer capacity for 100,000+ patients/year.',
              },
            ].map(({ icon: Icon, title, desc }) => (
              <div
                key={title}
                className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-6 text-left"
              >
                <Icon size={22} className="text-brand-400 mb-3" />
                <h3 className="font-semibold mb-1.5">{title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </main>

        <footer className="text-center text-xs text-slate-500 pb-6">
          RetinaScan District Screening Platform — for use alongside, not in place of, clinical judgement.
        </footer>
      </div>
    </div>
  );
}
