import React, { useState } from 'react';
import { Search, Video, Radio, Car, Play, Power, ExternalLink, RefreshCw, AlertTriangle } from 'lucide-react';

export default function LiveCamerasPage({ cameras, onSelectCamera, onToggleConnection }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('ALL');

  const filteredCameras = cameras.filter((cam) => {
    const matchesSearch = 
      cam.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (cam.name && cam.name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (cam.location && cam.location.toLowerCase().includes(searchTerm.toLowerCase()));

    const status = cam.connection_status || 'OFFLINE';
    const isLive = status === 'LIVE' || status === 'CONNECTED';
    if (filterStatus === 'ONLINE') return matchesSearch && (isLive || status === 'CONNECTING');
    if (filterStatus === 'OFFLINE') return matchesSearch && (!isLive && status !== 'CONNECTING');
    return matchesSearch;
  });

  const connectedCount = cameras.filter((c) => {
    const st = c.connection_status || 'OFFLINE';
    return st === 'LIVE' || st === 'CONNECTED' || st === 'CONNECTING';
  }).length;

  const renderStatusBadge = (status) => {
    switch (status) {
      case 'LIVE':
      case 'CONNECTED':
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded border uppercase bg-emerald-50 text-emerald-700 border-emerald-200 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" /> LIVE
          </span>
        );
      case 'CONNECTING':
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded border uppercase bg-sky-50 text-sky-700 border-sky-200 flex items-center gap-1">
            <RefreshCw className="w-2.5 h-2.5 animate-spin text-sky-600" /> CONNECTING
          </span>
        );
      case 'RECONNECTING':
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded border uppercase bg-amber-50 text-amber-800 border-amber-200 flex items-center gap-1">
            <RefreshCw className="w-2.5 h-2.5 animate-spin text-amber-600" /> RECONNECTING
          </span>
        );
      case 'STREAM_ERROR':
      case 'FRAME_DELIVERY_ERROR':
      case 'ERROR':
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded border uppercase bg-rose-50 text-rose-700 border-rose-200 flex items-center gap-1">
            <AlertTriangle className="w-2.5 h-2.5 text-rose-600" /> STREAM ERROR
          </span>
        );
      default:
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded border uppercase bg-slate-200 text-slate-600 border-slate-300">
            OFFLINE
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header Controls */}
      <div className="bg-white border border-slate-200 p-5 rounded-2xl card-shadow flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-[#12355B] uppercase tracking-wider flex items-center gap-2">
            <Video className="w-5 h-5 text-[#1976D2]" />
            Live CCTV Camera Matrix ({cameras.length} Feeds)
          </h2>
          <p className="text-xs text-slate-500 font-medium mt-0.5">
            Real-time traffic surveillance from connected Smart City CCTV locations
          </p>
        </div>

        {/* Search & Filter Pills */}
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search camera ID or location..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#1976D2]"
            />
          </div>

          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs font-semibold">
            <button
              onClick={() => setFilterStatus('ALL')}
              className={`px-3 py-1 rounded-md transition-all ${filterStatus === 'ALL' ? 'bg-[#1976D2] text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'}`}
            >
              ALL ({cameras.length})
            </button>
            <button
              onClick={() => setFilterStatus('ONLINE')}
              className={`px-3 py-1 rounded-md transition-all ${filterStatus === 'ONLINE' ? 'bg-emerald-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'}`}
            >
              ONLINE ({connectedCount})
            </button>
            <button
              onClick={() => setFilterStatus('OFFLINE')}
              className={`px-3 py-1 rounded-md transition-all ${filterStatus === 'OFFLINE' ? 'bg-slate-700 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'}`}
            >
              OFFLINE ({cameras.length - connectedCount})
            </button>
          </div>
        </div>
      </div>

      {/* Camera Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
        {filteredCameras.map((cam) => {
          const status = cam.connection_status || 'OFFLINE';
          const isConnected = status === 'LIVE' || status === 'CONNECTED' || status === 'CONNECTING';

          return (
            <div
              key={cam.id}
              className="bg-white border border-slate-200 hover:border-blue-300 rounded-2xl overflow-hidden shadow-xs flex flex-col group transition-all"
            >
              {/* Header */}
              <div className="p-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                <div className="flex items-center gap-2 min-w-0">
                  {renderStatusBadge(status)}
                  <span className="text-xs font-bold text-[#12355B] truncate">{cam.name || cam.id}</span>
                </div>
                <button
                  onClick={() => onToggleConnection(cam.id, !isConnected)}
                  className={`p-1.5 rounded-lg text-xs transition-all ${
                    isConnected
                      ? 'bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200'
                      : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200'
                  }`}
                  title={isConnected ? 'Disconnect Stream' : 'Connect Stream'}
                >
                  <Power className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Video Area */}
              <div
                onClick={() => onSelectCamera(cam)}
                className="relative aspect-video bg-slate-900 flex items-center justify-center cursor-pointer overflow-hidden"
              >
                {isConnected ? (
                  <img
                    src={`/api/cameras/${cam.id}/annotated`}
                    alt={`CCTV Stream ${cam.id}`}
                    className="w-full h-full object-cover group-hover:scale-[1.01] transition-transform duration-300"
                    onError={(e) => {
                      e.target.style.display = "none";
                      const errDiv = e.target.nextSibling;
                      if (errDiv) errDiv.style.display = "flex";
                    }}
                    onLoad={(e) => {
                      e.target.style.display = "block";
                      const errDiv = e.target.nextSibling;
                      if (errDiv) errDiv.style.display = "none";
                    }}
                  />
                ) : null}

                {/* Step 9: Informative Video Overlay Placeholder */}
                <div className={`${isConnected ? 'hidden' : 'flex'} absolute inset-0 bg-slate-100 flex flex-col items-center justify-center p-4 text-center text-slate-600`}>
                  <div className="p-3 bg-blue-50 rounded-full text-[#1976D2] mb-1.5">
                    <Video className="w-6 h-6 animate-pulse" />
                  </div>
                  <span className="text-xs font-bold text-[#12355B]">
                    {status === 'STREAM_ERROR' ? '⚠️ STREAM UNAVAILABLE' : '● CONNECTING TO LIVE CCTV'}
                  </span>
                  <span className="text-[10px] text-slate-500 mt-0.5">
                    {status === 'STREAM_ERROR' ? 'RTSP feed unreadable or authorization required' : 'Establishing secure video stream...'}
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onToggleConnection(cam.id, true);
                    }}
                    className="mt-2.5 px-3 py-1 bg-[#1976D2] hover:bg-blue-700 text-white text-[11px] font-semibold rounded-md transition-all shadow-xs flex items-center gap-1.5"
                  >
                    <RefreshCw className="w-3 h-3" /> Reconnect Camera
                  </button>
                </div>
              </div>

              {/* Bottom Info */}
              <div className="p-3 bg-white border-t border-slate-100 flex items-center justify-between text-xs text-slate-600 font-medium">
                <span className="flex items-center gap-1 font-semibold text-slate-700">
                  <Car className="w-3.5 h-3.5 text-[#1976D2]" />
                  Active Stream
                </span>
                <span className="text-emerald-700 font-semibold">Traffic: LOW</span>
                <button
                  onClick={() => onSelectCamera(cam)}
                  className="text-xs font-semibold text-[#1976D2] hover:underline flex items-center gap-1"
                >
                  View Details <ExternalLink className="w-3 h-3" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
