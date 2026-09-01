import React from 'react';
import { BarChart3, Car, Bike, Bus, Truck, Activity, TrendingUp, CheckCircle2 } from 'lucide-react';

export default function TrafficAnalyticsPage({ analyticsList, analyticsSummary }) {
  const totalActiveVehicles = analyticsSummary?.total_active_vehicles || 0;
  const busiestCamera = analyticsSummary?.busiest_camera || 'cam04';
  const highestActiveCount = analyticsSummary?.highest_active_vehicle_count || 0;
  const densitySummary = analyticsSummary?.traffic_density_summary || { LOW: 0, MODERATE: 0, HIGH: 0, VERY_HIGH: 0 };

  // Aggregate vehicle types across all active camera analytics
  let totalCars = 0;
  let totalMotorcycles = 0;
  let totalBuses = 0;
  let totalTrucks = 0;

  if (Array.isArray(analyticsList)) {
    analyticsList.forEach((an) => {
      const breakdown = an.unique_vehicle_breakdown || {};
      totalCars += breakdown.cars || 0;
      totalMotorcycles += breakdown.motorcycles || 0;
      totalBuses += breakdown.buses || 0;
      totalTrucks += breakdown.trucks || 0;
    });
  }

  const grandTotalTracked = totalCars + totalMotorcycles + totalBuses + totalTrucks;
  const carPct = grandTotalTracked > 0 ? Math.round((totalCars / grandTotalTracked) * 100) : 0;
  const motoPct = grandTotalTracked > 0 ? Math.round((totalMotorcycles / grandTotalTracked) * 100) : 0;
  const busPct = grandTotalTracked > 0 ? Math.round((totalBuses / grandTotalTracked) * 100) : 0;
  const truckPct = grandTotalTracked > 0 ? Math.round((totalTrucks / grandTotalTracked) * 100) : 0;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Title */}
      <div className="bg-white border border-slate-200 p-5 rounded-2xl card-shadow flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-[#12355B] uppercase tracking-wider flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-[#1976D2]" />
            Smart City Traffic Analytics & Flow Visualization
          </h2>
          <p className="text-xs text-slate-500 font-medium mt-0.5">
            Aggregated traffic statistics, vehicle class distribution, and camera comparison
          </p>
        </div>
        <span className="px-3 py-1.5 text-xs font-mono font-semibold bg-blue-50 text-blue-800 border border-blue-200 rounded-lg">
          Live Telemetry Active
        </span>
      </div>

      {/* Top Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white border border-slate-200 p-5 rounded-2xl card-shadow flex items-center gap-4">
          <div className="p-3.5 bg-blue-50 border border-blue-100 rounded-2xl text-[#1976D2]">
            <Car className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">Total Active Vehicles</span>
            <span className="text-2xl font-extrabold text-[#12355B] font-mono">{totalActiveVehicles}</span>
          </div>
        </div>

        <div className="bg-white border border-slate-200 p-5 rounded-2xl card-shadow flex items-center gap-4">
          <div className="p-3.5 bg-indigo-50 border border-indigo-100 rounded-2xl text-indigo-600">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">Busiest CCTV Location</span>
            <span className="text-xl font-bold text-indigo-900 font-mono">{busiestCamera} ({highestActiveCount} in view)</span>
          </div>
        </div>

        <div className="bg-white border border-slate-200 p-5 rounded-2xl card-shadow flex items-center gap-4">
          <div className="p-3.5 bg-emerald-50 border border-emerald-100 rounded-2xl text-emerald-600">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">System Traffic Status</span>
            <span className="text-xl font-extrabold text-emerald-700 font-mono">LOW / NORMAL</span>
          </div>
        </div>
      </div>

      {/* Visual Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Vehicle Distribution Progress Bars */}
        <div className="bg-white border border-slate-200 p-5 rounded-2xl card-shadow space-y-4">
          <h3 className="text-sm font-bold text-[#12355B] uppercase tracking-wider flex items-center gap-2">
            <Car className="w-4 h-4 text-[#1976D2]" />
            Vehicle Class Distribution
          </h3>

          <div className="space-y-4">
            {/* Cars */}
            <div>
              <div className="flex justify-between text-xs mb-1.5 font-semibold">
                <span className="text-slate-700 flex items-center gap-1.5"><Car className="w-4 h-4 text-[#1976D2]" /> Cars</span>
                <span className="text-slate-900 font-mono">{totalCars} ({carPct}%)</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                <div className="bg-[#1976D2] h-full rounded-full transition-all duration-500" style={{ width: `${carPct}%` }} />
              </div>
            </div>

            {/* Motorcycles */}
            <div>
              <div className="flex justify-between text-xs mb-1.5 font-semibold">
                <span className="text-slate-700 flex items-center gap-1.5"><Bike className="w-4 h-4 text-emerald-600" /> Motorcycles</span>
                <span className="text-slate-900 font-mono">{totalMotorcycles} ({motoPct}%)</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                <div className="bg-emerald-600 h-full rounded-full transition-all duration-500" style={{ width: `${motoPct}%` }} />
              </div>
            </div>

            {/* Buses */}
            <div>
              <div className="flex justify-between text-xs mb-1.5 font-semibold">
                <span className="text-slate-700 flex items-center gap-1.5"><Bus className="w-4 h-4 text-amber-600" /> Buses</span>
                <span className="text-slate-900 font-mono">{totalBuses} ({busPct}%)</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                <div className="bg-amber-500 h-full rounded-full transition-all duration-500" style={{ width: `${busPct}%` }} />
              </div>
            </div>

            {/* Trucks */}
            <div>
              <div className="flex justify-between text-xs mb-1.5 font-semibold">
                <span className="text-slate-700 flex items-center gap-1.5"><Truck className="w-4 h-4 text-indigo-600" /> Trucks</span>
                <span className="text-slate-900 font-mono">{totalTrucks} ({truckPct}%)</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                <div className="bg-indigo-600 h-full rounded-full transition-all duration-500" style={{ width: `${truckPct}%` }} />
              </div>
            </div>
          </div>
        </div>

        {/* Traffic Density Breakdown Cards */}
        <div className="bg-white border border-slate-200 p-5 rounded-2xl card-shadow space-y-4">
          <h3 className="text-sm font-bold text-[#12355B] uppercase tracking-wider flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-600" />
            Traffic Density Distribution
          </h3>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-emerald-50/70 rounded-2xl border border-emerald-200 text-center">
              <span className="text-xs text-emerald-800 font-semibold block mb-1">LOW DENSITY</span>
              <span className="text-2xl font-extrabold text-emerald-700 font-mono">{densitySummary.LOW || 0}</span>
              <span className="text-[10px] text-emerald-600 block mt-1">0 - 5 active vehicles</span>
            </div>

            <div className="p-4 bg-yellow-50/70 rounded-2xl border border-yellow-200 text-center">
              <span className="text-xs text-yellow-800 font-semibold block mb-1">MODERATE DENSITY</span>
              <span className="text-2xl font-extrabold text-yellow-700 font-mono">{densitySummary.MODERATE || 0}</span>
              <span className="text-[10px] text-yellow-600 block mt-1">6 - 15 active vehicles</span>
            </div>

            <div className="p-4 bg-amber-50/70 rounded-2xl border border-amber-200 text-center">
              <span className="text-xs text-amber-800 font-semibold block mb-1">HIGH DENSITY</span>
              <span className="text-2xl font-extrabold text-amber-700 font-mono">{densitySummary.HIGH || 0}</span>
              <span className="text-[10px] text-amber-600 block mt-1">16 - 30 active vehicles</span>
            </div>

            <div className="p-4 bg-rose-50/70 rounded-2xl border border-rose-200 text-center">
              <span className="text-xs text-rose-800 font-semibold block mb-1">VERY HIGH DENSITY</span>
              <span className="text-2xl font-extrabold text-rose-700 font-mono">{densitySummary.VERY_HIGH || 0}</span>
              <span className="text-[10px] text-rose-600 block mt-1">31+ active vehicles</span>
            </div>
          </div>
        </div>
      </div>

      {/* Camera Comparison Table */}
      <div className="bg-white border border-slate-200 p-5 rounded-2xl card-shadow space-y-4 overflow-x-auto">
        <h3 className="text-sm font-bold text-[#12355B] uppercase tracking-wider">Per-Camera Analytics Comparison</h3>

        {Array.isArray(analyticsList) && analyticsList.length > 0 ? (
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-50 text-slate-600 border-b border-slate-200 font-semibold">
                <th className="p-3.5">Camera ID</th>
                <th className="p-3.5">Active Vehicles</th>
                <th className="p-3.5">Total Unique</th>
                <th className="p-3.5">Flow Rate (VPM)</th>
                <th className="p-3.5">Traffic Density</th>
                <th className="p-3.5">Stationary Vehicles</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {analyticsList.map((an) => (
                <tr key={an.camera_id} className="hover:bg-slate-50 transition-colors">
                  <td className="p-3.5 font-bold text-[#1976D2] font-mono">{an.camera_id}</td>
                  <td className="p-3.5 font-bold text-slate-800 font-mono">{an.active_vehicles}</td>
                  <td className="p-3.5 text-slate-600 font-mono">{an.total_unique_vehicles}</td>
                  <td className="p-3.5 text-emerald-700 font-mono font-semibold">{an.flow_metrics?.vehicles_per_minute || 0.0} VPM</td>
                  <td className="p-3.5">
                    <span className="px-2.5 py-0.5 text-[11px] font-bold rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {an.traffic_density}
                    </span>
                  </td>
                  <td className="p-3.5 text-slate-600 font-mono">{an.stationary_vehicles?.length || 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="p-8 text-center text-slate-500 text-xs">
            No camera analytics streams currently connected. Start streams in Live Cameras tab.
          </div>
        )}
      </div>
    </div>
  );
}
