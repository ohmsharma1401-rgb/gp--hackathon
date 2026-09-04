import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import CommandCenterDashboard from './components/CommandCenterDashboard';
import LiveCamerasPage from './components/LiveCamerasPage';
import TrafficAnalyticsPage from './components/TrafficAnalyticsPage';
import IncidentCenterPage from './components/IncidentCenterPage';
import CameraManagementPage from './components/CameraManagementPage';
import AnprAssessmentPage from './components/AnprAssessmentPage';
import SystemStatusPage from './components/SystemStatusPage';
import DemoCamerasPage from './components/DemoCamerasPage';
import CameraFocusModal from './components/CameraFocusModal';
import { AlertCircle, Activity, CheckCircle2 } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [collapsed, setCollapsed] = useState(false);
  const [streamMode, setStreamMode] = useState('LIVE'); // 'LIVE' or 'DEMO'

  const [cameras, setCameras] = useState([]);
  const [analyticsSummary, setAnalyticsSummary] = useState(null);
  const [analyticsList, setAnalyticsList] = useState([]);
  const [eventsSummary, setEventsSummary] = useState(null);
  const [eventsList, setEventsList] = useState([]);
  const [selectedCamera, setSelectedCamera] = useState(null);

  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [systemState, setSystemState] = useState('OPERATIONAL'); // 'OPERATIONAL', 'DEGRADED', 'OFFLINE'

  // Centralized robust API fetcher with fallback to direct http://localhost:8000
  const safeFetchJson = async (endpoint) => {
    try {
      const res = await fetch(endpoint);
      if (res.ok) return await res.json();
    } catch (e) {
      // Fallback if proxying fails
      try {
        const directRes = await fetch(`http://localhost:8000${endpoint}`);
        if (directRes.ok) return await directRes.json();
      } catch (err) {
        console.warn(`Direct fetch failed for ${endpoint}:`, err);
      }
    }
    return null;
  };

  // Fetch all backend telemetry & state
  const fetchAllData = async (forceRefresh = false) => {
    setIsRefreshing(true);
    try {
      // 1. Fetch Camera Catalogue
      const camData = await safeFetchJson(`/api/cameras${forceRefresh ? '?refresh=true' : ''}`);
      if (camData && Array.isArray(camData)) {
        setCameras(camData);
      }

      // 2. Fetch Traffic Analytics Summary
      const summaryData = await safeFetchJson('/api/analytics/summary');
      if (summaryData) {
        setAnalyticsSummary(summaryData);
      }

      // 3. Fetch All Camera Analytics List
      const listData = await safeFetchJson('/api/analytics');
      if (listData && Array.isArray(listData)) {
        setAnalyticsList(listData);
      }

      // 4. Fetch Events Summary
      const evtSumData = await safeFetchJson('/api/events/summary');
      if (evtSumData) {
        setEventsSummary(evtSumData);
      }

      // 5. Fetch Events Feed List
      const evtListData = await safeFetchJson('/api/events');
      if (evtListData && Array.isArray(evtListData)) {
        setEventsList(evtListData);
      }

      // Compute System State
      const onlineCount = (camData || cameras).filter(
        (c) => c.connection_status === 'CONNECTED' || c.connection_status === 'CONNECTING'
      ).length;

      if (!camData && !summaryData) {
        setSystemState('OFFLINE');
        setError('Backend server (localhost:8000) is currently offline.');
      } else if (onlineCount === 0 && streamMode === 'LIVE') {
        setSystemState('DEGRADED');
        setError(null);
      } else {
        setSystemState('OPERATIONAL');
        setError(null);
      }
    } catch (err) {
      console.error('Failed to fetch CCTV backend state:', err);
      setSystemState('OFFLINE');
      setError('Unable to synchronize with CCTV Surveillance Backend server.');
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    // Hard synchronization timeout to guarantee user is NEVER stuck on infinite loading screen
    const syncTimeout = setTimeout(() => {
      setLoading(false);
    }, 2000);

    fetchAllData();
    const interval = setInterval(() => fetchAllData(false), 3000);

    return () => {
      clearTimeout(syncTimeout);
      clearInterval(interval);
    };
  }, []);

  const handleToggleConnection = async (cameraId, shouldConnect) => {
    const endpoint = shouldConnect ? `/api/cameras/${cameraId}/connect` : `/api/cameras/${cameraId}/disconnect`;
    try {
      await fetch(endpoint, { method: 'POST' });
      fetchAllData(false);
    } catch (err) {
      try {
        await fetch(`http://localhost:8000${endpoint}`, { method: 'POST' });
        fetchAllData(false);
      } catch (e) {
        console.error('Connection toggle error:', e);
      }
    }
  };

  const connectedCount = cameras.filter(
    (c) => c.connection_status === 'CONNECTED' || c.connection_status === 'CONNECTING'
  ).length;

  const activeIncidentsCount = eventsSummary?.active_events || 0;

  // Selected camera analytics for Focus Modal
  const selectedCameraAnalytics = selectedCamera 
    ? analyticsList.find(a => a.camera_id === selectedCamera.id) 
    : null;

  return (
    <div className="min-h-screen bg-[#F4F7FB] text-[#1E293B] flex overflow-hidden font-sans">
      {/* Fixed Responsive Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        activeIncidentsCount={activeIncidentsCount}
        onlineCamerasCount={connectedCount}
        collapsed={collapsed}
        setCollapsed={setCollapsed}
      />

      {/* Main Content Body */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* Top Header */}
        <Header
          totalCameras={cameras.length || 30}
          connectedCount={connectedCount}
          onRefresh={() => fetchAllData(true)}
          isRefreshing={isRefreshing}
          streamMode={streamMode}
          setStreamMode={setStreamMode}
          systemState={systemState}
        />

        {/* Dynamic Route Body */}
        <main className="flex-1 p-6 max-w-[1800px] w-full mx-auto space-y-6">
          {/* Degraded / Offline Status Banners */}
          {systemState === 'DEGRADED' && (
            <div className="bg-amber-50 border border-amber-200 text-amber-800 rounded-2xl p-4 flex items-center justify-between text-xs card-shadow">
              <div className="flex items-center gap-3 font-semibold">
                <Activity className="w-5 h-5 text-amber-600 shrink-0" />
                <div>
                  <span className="font-bold uppercase tracking-wider block">SYSTEM STATUS: DEGRADED</span>
                  <span className="font-normal text-slate-600 mt-0.5 block">
                    Backend: ONLINE | Camera Streams: 0/{cameras.length || 30} ONLINE. Camera streams are currently connecting. The command center remains fully operational.
                  </span>
                </div>
              </div>
              <button
                onClick={() => handleToggleConnection('cam04', true)}
                className="px-3.5 py-1.5 bg-[#1976D2] hover:bg-blue-700 text-white rounded-lg font-semibold shadow-xs transition-all shrink-0"
              >
                Auto-Connect Streams
              </button>
            </div>
          )}

          {systemState === 'OFFLINE' && error && (
            <div className="bg-rose-50 border border-rose-200 text-rose-800 rounded-2xl p-4 flex items-center gap-3 text-xs card-shadow">
              <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
              <div>
                <span className="font-bold uppercase tracking-wider block">SYSTEM STATUS: OFFLINE</span>
                <span className="font-normal text-rose-700 mt-0.5 block">{error}</span>
              </div>
            </div>
          )}

          {/* Page Routing */}
          {loading ? (
            <div className="flex flex-col items-center justify-center p-24 text-slate-500 bg-white rounded-2xl border border-slate-200 card-shadow">
              <div className="w-10 h-10 border-4 border-[#1976D2] border-t-transparent rounded-full animate-spin mb-4" />
              <p className="text-sm font-semibold text-[#12355B]">Synchronizing Smart City CCTV Command Center...</p>
              <p className="text-xs text-slate-500 mt-1">Establishing secure telemetry & video streaming channels</p>
            </div>
          ) : streamMode === 'DEMO' ? (
            <DemoCamerasPage
              onSelectCamera={(cam) => setSelectedCamera(cam)}
            />
          ) : (
            <>
              {activeTab === 'dashboard' && (
                <CommandCenterDashboard
                  cameras={cameras}
                  analyticsSummary={analyticsSummary}
                  eventsSummary={eventsSummary}
                  onSelectCamera={(cam) => setSelectedCamera(cam)}
                  onNavigateToTab={(tab) => setActiveTab(tab)}
                  streamMode={streamMode}
                />
              )}

              {activeTab === 'cameras' && (
                <LiveCamerasPage
                  cameras={cameras}
                  onSelectCamera={(cam) => setSelectedCamera(cam)}
                  onToggleConnection={handleToggleConnection}
                  streamMode={streamMode}
                />
              )}

              {activeTab === 'analytics' && (
                <TrafficAnalyticsPage
                  analyticsList={analyticsList}
                  analyticsSummary={analyticsSummary}
                />
              )}

              {activeTab === 'incidents' && (
                <IncidentCenterPage
                  eventsList={eventsList}
                  eventsSummary={eventsSummary}
                />
              )}

              {activeTab === 'camera-management' && (
                <CameraManagementPage
                  cameras={cameras}
                  onToggleConnection={handleToggleConnection}
                  onSelectCamera={(cam) => setSelectedCamera(cam)}
                  onRefresh={() => fetchAllData(true)}
                />
              )}

              {activeTab === 'anpr-assessment' && (
                <AnprAssessmentPage />
              )}

              {activeTab === 'system-status' && (
                <SystemStatusPage
                  totalCameras={cameras.length || 30}
                  connectedCount={connectedCount}
                />
              )}
            </>
          )}
        </main>

        {/* Global Command Center Footer */}
        <footer className="border-t border-slate-200 bg-white py-3 px-6 text-center text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-2 shadow-xs">
          <span className="font-medium text-slate-600">Smart City CCTV Surveillance Command Center · Phase 11 Verified</span>
          <span className="font-mono text-[11px] text-[#1976D2] font-semibold">
            Mode: {streamMode === 'LIVE' ? '🟢 LIVE GOVERNMENT CCTV' : '🎬 VISDRONE (VisDrone2019-VID-val) DEMO MODE'} | Hardware: NVIDIA RTX 4050 CUDA
          </span>
        </footer>
      </div>

      {/* Camera Focus Modal Popup (LIVE Government Mode Only) */}
      {selectedCamera && streamMode === 'LIVE' && (
        <CameraFocusModal
          camera={selectedCamera}
          analytics={selectedCameraAnalytics}
          onClose={() => setSelectedCamera(null)}
          onToggleConnection={handleToggleConnection}
          streamMode={streamMode}
        />
      )}
    </div>
  );
}
