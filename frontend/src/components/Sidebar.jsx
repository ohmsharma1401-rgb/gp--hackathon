import React from 'react';
import { 
  LayoutDashboard, 
  Video, 
  BarChart3, 
  AlertTriangle, 
  Sliders, 
  SearchCode, 
  Activity, 
  ShieldCheck, 
  ChevronLeft, 
  ChevronRight 
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, activeIncidentsCount, onlineCamerasCount, collapsed, setCollapsed }) {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'cameras', label: 'Live Cameras', icon: Video, badge: `${onlineCamerasCount} Live` },
    { id: 'analytics', label: 'Traffic Analytics', icon: BarChart3 },
    { 
      id: 'incidents', 
      label: 'Incident Center', 
      icon: AlertTriangle, 
      badge: activeIncidentsCount > 0 ? `${activeIncidentsCount} Active` : null,
      badgeColor: activeIncidentsCount > 0 ? 'bg-rose-100 text-rose-700 font-bold' : ''
    },
    { id: 'camera-management', label: 'Camera Management', icon: Sliders },
    { id: 'anpr-assessment', label: 'ANPR Assessment', icon: SearchCode },
    { id: 'system-status', label: 'System Status', icon: Activity },
  ];

  return (
    <aside className={`${collapsed ? 'w-20' : 'w-64'} bg-white border-r border-slate-200 flex flex-col transition-all duration-300 z-30 shrink-0 shadow-sm`}>
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-100 flex items-center justify-between">
        {!collapsed && (
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[#EAF4FF] border border-[#1976D2]/20 rounded-xl text-[#1976D2]">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-[#12355B] tracking-tight uppercase">SMART CITY CCTV</h1>
              <p className="text-[10px] text-slate-500 font-medium leading-tight">Unified Surveillance & Traffic Monitoring</p>
            </div>
          </div>
        )}
        {collapsed && (
          <div className="mx-auto p-2 bg-[#EAF4FF] border border-[#1976D2]/20 rounded-xl text-[#1976D2]">
            <ShieldCheck className="w-6 h-6" />
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="hidden md:flex p-1.5 rounded-lg bg-slate-50 text-slate-500 hover:text-slate-800 hover:bg-slate-100 border border-slate-200 transition-colors"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center ${collapsed ? 'justify-center px-0' : 'justify-between px-3.5'} py-2.5 rounded-xl text-xs transition-all ${
                isActive
                  ? 'bg-[#EAF4FF] text-[#1976D2] font-bold shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50 font-medium'
              }`}
              title={collapsed ? item.label : ''}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-[#1976D2]' : 'text-slate-500'}`} />
                {!collapsed && <span>{item.label}</span>}
              </div>
              {!collapsed && item.badge && (
                <span className={`px-2 py-0.5 text-[10px] rounded-full font-medium ${item.badgeColor || 'bg-blue-50 text-blue-700 border border-blue-200'}`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer System Operational Badge */}
      {!collapsed && (
        <div className="p-4 border-t border-slate-100 bg-slate-50/50">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-600 mb-1">
            <span>System Status</span>
            <span className="text-emerald-700 font-bold flex items-center gap-1.5 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200 text-[11px]">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-live-pulse" />
              Operational
            </span>
          </div>
          <p className="text-[10px] text-slate-500 font-mono mt-1">
            Smart City Control Room v1.0
          </p>
        </div>
      )}
    </aside>
  );
}
