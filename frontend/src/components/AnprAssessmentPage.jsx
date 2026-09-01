import React from 'react';
import { SearchCode, CheckCircle2, AlertTriangle, ShieldCheck, FileCheck, Check } from 'lucide-react';

export default function AnprAssessmentPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Title */}
      <div className="bg-white border border-slate-200 p-5 rounded-2xl card-shadow flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-[#12355B] uppercase tracking-wider flex items-center gap-2">
            <SearchCode className="w-5 h-5 text-amber-500" />
            License Plate Recognition Assessment
          </h2>
          <p className="text-xs text-slate-500 font-medium mt-0.5">
            Empirical scientific evaluation of ANPR performance across public CCTV infrastructure
          </p>
        </div>
        <span className="px-3.5 py-1.5 text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200 rounded-lg">
          Current Capability Status: Evaluation Complete
        </span>
      </div>

      {/* Current Capability Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* 1. Vehicle Detection */}
        <div className="bg-white border border-emerald-200 p-5 rounded-2xl card-shadow space-y-3">
          <div className="flex items-center gap-2 text-emerald-700 font-bold text-sm">
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            <h3>Vehicle Detection</h3>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 bg-emerald-50 text-emerald-700 rounded-md border border-emerald-200 inline-block">
            🟢 AVAILABLE
          </span>
          <p className="text-xs text-slate-600 leading-relaxed font-medium">
            Automated detection of cars, motorcycles, buses, and trucks operating cleanly on NVIDIA RTX 4050 GPU.
          </p>
        </div>

        {/* 2. Vehicle Tracking */}
        <div className="bg-white border border-emerald-200 p-5 rounded-2xl card-shadow space-y-3">
          <div className="flex items-center gap-2 text-emerald-700 font-bold text-sm">
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            <h3>Vehicle Tracking</h3>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 bg-emerald-50 text-emerald-700 rounded-md border border-emerald-200 inline-block">
            🟢 AVAILABLE
          </span>
          <p className="text-xs text-slate-600 leading-relaxed font-medium">
            ByteTrack multi-object tracking maintains persistent track IDs for accurate traffic counting and trajectory analysis.
          </p>
        </div>

        {/* 3. License Plate OCR */}
        <div className="bg-white border border-amber-200 p-5 rounded-2xl card-shadow space-y-3">
          <div className="flex items-center gap-2 text-amber-700 font-bold text-sm">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            <h3>License Plate OCR</h3>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 bg-amber-50 text-amber-800 rounded-md border border-amber-200 inline-block">
            ⚠️ LIMITED BY RESOLUTION
          </span>
          <p className="text-xs text-slate-600 leading-relaxed font-medium">
            Character pixel height is below the 25px minimum required for OCR due to wide-angle camera distance on public streams.
          </p>
        </div>
      </div>

      {/* Explanation Banner */}
      <div className="bg-slate-50 border border-slate-200 rounded-2xl p-6 space-y-2 card-shadow">
        <h3 className="text-sm font-bold text-[#12355B] flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-[#1976D2]" />
          Infrastructure Assessment Findings
        </h3>
        <p className="text-xs text-slate-600 leading-relaxed font-medium">
          The currently available wide-angle CCTV infrastructure is optimized for area surveillance and traffic monitoring. License plate character resolution is insufficient for reliable OCR on the tested live feeds.
        </p>
      </div>

      {/* Technical Validation Breakdown */}
      <div className="bg-white border border-slate-200 p-6 rounded-2xl card-shadow space-y-4">
        <h3 className="text-sm font-bold text-[#12355B] uppercase tracking-wider flex items-center gap-2">
          <FileCheck className="w-4 h-4 text-[#1976D2]" />
          Technical Validation Summary
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-semibold">
          <div className="p-4 bg-emerald-50/60 border border-emerald-200 rounded-xl space-y-2 text-emerald-800">
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-600" />
              <span>ANPR Pipeline Successfully Implemented</span>
            </div>
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-600" />
              <span>Plate Detection Tested & Verified</span>
            </div>
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-600" />
              <span>OCR Pipeline Tested & Verified</span>
            </div>
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-600" />
              <span>Controlled Video Validation Successful</span>
            </div>
          </div>

          <div className="p-4 bg-amber-50/60 border border-amber-200 rounded-xl space-y-2 text-amber-800">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <span>Live Government Feed OCR Limited by Camera Distance & Resolution</span>
            </div>
            <p className="text-[11px] text-slate-600 font-normal leading-relaxed pt-1">
              Data Integrity Rule Enforced: Zero hallucinated or fabricated registration numbers displayed on public feeds.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
