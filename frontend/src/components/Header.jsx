import React, { useState, useEffect } from 'react';
import { RefreshCw, Clock, Video, CheckCircle2, AlertTriangle, PlayCircle } from 'lucide-react';

export default function Header({ 
  totalCameras, 
  connectedCount, 
  onRefresh, 
  isRefreshing,
  streamMode,
  setStreamMode,
  systemState = 'OPERATIONAL'
}) {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="bg-white border-b border-slate-200 px-6 py-3.5 flex flex-col md:flex-row md:items-center justify-between gap-4 sticky top-0 z-20 shadow-xs">
      {/* Left Title & Subtitle */}
      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-bold text-[#12355B] tracking-tight">
            Smart City CCTV Command Center
          </h1>
          {/* Mode Switcher Pill */}
          <div className="flex items-center bg-slate-100 p-0.5 rounded-lg border border-slate-200 text-[11px] font-semibold">
            <button
              onClick={() => setStreamMode('LIVE')}
              className={`px-2.5 py-1 rounded-md transition-all flex items-center gap-1 ${
                streamMode === 'LIVE' ? 'bg-[#1976D2] text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-live-pulse" />
              LIVE CCTV
            </button>
            <button
              onClick={() => setStreamMode('DEMO')}
              className={`px-2.5 py-1 rounded-md transition-all flex items-center gap-1 ${
                streamMode === 'DEMO' ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <PlayCircle className="w-3 h-3" />
              DEMO MODE
            </button>
          </div>
        </div>
        <p className="text-[11px] text-slate-500 mt-0.5 font-medium">
          Real-Time Traffic Surveillance & Monitoring Infrastructure
        </p>
      </div>

      {/* Right Badges & Actions */}
      <div className="flex flex-wrap items-center gap-2.5 text-xs">
        {/* System Operational/Degraded Badge */}
        {systemState === 'OPERATIONAL' && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 font-semibold">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>System Operational</span>
          </div>
        )}

        {systemState === 'DEGRADED' && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 font-semibold">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <span>System Degraded</span>
          </div>
        )}

        {systemState === 'OFFLINE' && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 font-semibold">
            <AlertTriangle className="w-4 h-4 text-rose-600" />
            <span>Backend Offline</span>
          </div>
        )}

        {/* Cameras Status Badge */}
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-50 border border-blue-200 text-blue-800 font-semibold">
          <Video className="w-4 h-4 text-[#1976D2]" />
          <span>{connectedCount} / {totalCameras} Cameras Online</span>
        </div>

        {/* Current Time */}
        <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-700 font-medium font-mono text-[11px]">
          <Clock className="w-3.5 h-3.5 text-slate-500" />
          <span>{time.toLocaleTimeString()}</span>
        </div>

        {/* Refresh Button */}
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#1976D2] hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
          <span>{isRefreshing ? 'Syncing...' : 'Sync'}</span>
        </button>
      </div>
    </header>
  );
}
