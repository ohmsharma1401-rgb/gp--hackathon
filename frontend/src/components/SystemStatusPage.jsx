import React from 'react';
import { Activity, Cpu, CheckCircle2, Server, HardDrive, ShieldCheck, AlertTriangle } from 'lucide-react';

export default function SystemStatusPage({ totalCameras, connectedCount, gpuName = "NVIDIA GeForce RTX 4050 Laptop GPU" }) {
  const systemComponents = [
    { name: "CCTV Network Stream Workers", status: "Operational", icon: Server, color: "emerald", detail: "OpenCV RTSP Ingestion · Bounded Ring Buffers" },
    { name: "Hardware Acceleration", status: "Active (cuda:0)", icon: Cpu, color: "emerald", detail: gpuName },
    { name: "AI Vehicle Detection Engine", status: "Operational", icon: CheckCircle2, color: "emerald", detail: "YOLOv8 FP16 CUDA PyTorch 2.6.0+cu124" },
    { name: "Vehicle Tracking Engine", status: "Operational", icon: CheckCircle2, color: "emerald", detail: "ByteTrack Multi-Object Persistent Track IDs" },
    { name: "Traffic Analytics Engine", status: "Operational", icon: Activity, color: "emerald", detail: "Unique vehicle counters & flow rate analytics" },
    { name: "Incident Detection Engine", status: "Operational", icon: AlertTriangle, color: "emerald", detail: "Trajectory vector & stationary behavior rules" },
    { name: "License Plate Recognition (ANPR)", status: "Limited by Resolution", icon: ShieldCheck, color: "amber", detail: "Wide-angle camera mounting constraint" },
    { name: "FastAPI REST API Service", status: "Operational", icon: HardDrive, color: "emerald", detail: "Uvicorn ASGI Server on Port 8000" },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Title */}
      <div className="bg-white border border-slate-200 p-5 rounded-2xl card-shadow flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-[#12355B] uppercase tracking-wider flex items-center gap-2">
            <Activity className="w-5 h-5 text-emerald-600" />
            System Status & Technical Diagnostics
          </h2>
          <p className="text-xs text-slate-500 font-medium mt-0.5">
            Detailed operational metrics for AI detection engines, GPU hardware, and backend infrastructure
          </p>
        </div>

        <span className="px-3.5 py-1.5 text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-lg flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-live-pulse" />
          ALL SYSTEMS OPERATIONAL
        </span>
      </div>

      {/* Component Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {systemComponents.map((comp, idx) => {
          const Icon = comp.icon;
          const isEmerald = comp.color === 'emerald';

          return (
            <div
              key={idx}
              className="bg-white border border-slate-200 p-4 rounded-2xl card-shadow card-shadow-hover space-y-3 flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className={`p-2 rounded-xl border ${isEmerald ? 'bg-emerald-50 text-emerald-600 border-emerald-200' : 'bg-amber-50 text-amber-600 border-amber-200'}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className={`px-2 py-0.5 text-[10px] font-bold font-mono rounded border ${
                    isEmerald
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : 'bg-amber-50 text-amber-800 border-amber-200'
                  }`}>
                    ● {comp.status}
                  </span>
                </div>

                <h3 className="text-xs font-bold text-[#12355B]">{comp.name}</h3>
                <p className="text-[11px] text-slate-500 font-mono font-medium">{comp.detail}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Hardware Telemetry Card */}
      <div className="bg-white border border-slate-200 p-5 rounded-2xl card-shadow space-y-3">
        <h3 className="text-xs font-bold text-[#12355B] uppercase tracking-wider">GPU & Network Telemetry</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
            <span className="text-slate-500 font-medium block mb-1">Computation Device</span>
            <span className="text-sm font-bold text-[#12355B] font-mono">{gpuName}</span>
          </div>
          <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
            <span className="text-slate-500 font-medium block mb-1">CCTV Streams Ingestion</span>
            <span className="text-sm font-bold text-emerald-700 font-mono">{connectedCount} Active / {totalCameras} Catalogue Feeds</span>
          </div>
          <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
            <span className="text-slate-500 font-medium block mb-1">Stream Transport Standard</span>
            <span className="text-sm font-bold text-[#1976D2] font-mono">RTSP over TCP (OpenCV FFMPEG)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
