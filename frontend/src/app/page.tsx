'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Play, Pause, RotateCcw, Activity, TrendingUp, Zap, Radio, Network } from 'lucide-react';

interface MetricsData {
  timestamp: string;
  total_traffic_generated: number;
  total_packets_processed: number;
  total_packets_dropped: number;
  slice_metrics: Record<string, any>;
}

interface SimulationState {
  simulation_id: string | null;
  isRunning: boolean;
  metrics: MetricsData | null;
  connectionStatus: 'connected' | 'disconnected' | 'connecting';
}

export default function Dashboard() {
  const [state, setState] = useState<SimulationState>({
    simulation_id: null,
    isRunning: false,
    metrics: null,
    connectionStatus: 'disconnected',
  });

  const [trafficVolume, setTrafficVolume] = useState(5000);
  const [duration, setDuration] = useState(120);
  const [pattern, setPattern] = useState('wave');
  const ws = useRef<WebSocket | null>(null);

  const connectWebSocket = useCallback((simulationId: string) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.close();
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws.current = new WebSocket(`${protocol}//localhost:8000/ws/metrics/${simulationId}`);

    ws.current.onopen = () => {
      setState((prev) => ({ ...prev, connectionStatus: 'connected' }));
    };

    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'metrics_update') {
          setState((prev) => ({ ...prev, metrics: data.data }));
        }
      } catch (e) {
        console.error('Error:', e);
      }
    };

    ws.current.onerror = () => {
      setState((prev) => ({ ...prev, connectionStatus: 'disconnected' }));
    };

    ws.current.onclose = () => {
      setState((prev) => ({ ...prev, connectionStatus: 'disconnected' }));
    };
  }, []);

  const startSimulation = async () => {
    try {
      const createRes = await fetch('http://localhost:8000/simulation/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          traffic_volume: trafficVolume,
          duration,
          pattern,
          interval: 1,
        }),
      });

      const createData = await createRes.json();
      const simId = createData.simulation_id;

      setState((prev) => ({
        ...prev,
        simulation_id: simId,
        isRunning: false,
      }));

      connectWebSocket(simId);

      const startRes = await fetch(`http://localhost:8000/simulation/${simId}/start`, {
        method: 'POST',
      });

      if (startRes.ok) {
        setState((prev) => ({ ...prev, isRunning: true }));
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to start simulation');
    }
  };

  const stopSimulation = async () => {
    if (!state.simulation_id) return;

    try {
      await fetch(`http://localhost:8000/simulation/${state.simulation_id}/stop`, {
        method: 'POST',
      });
      setState((prev) => ({ ...prev, isRunning: false }));
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const resetSimulation = () => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.close();
    }
    setState({
      simulation_id: null,
      isRunning: false,
      metrics: null,
      connectionStatus: 'disconnected',
    });
  };

  const successRate = state.metrics
    ? ((state.metrics.total_packets_processed - state.metrics.total_packets_dropped) /
        state.metrics.total_traffic_generated) *
      100
    : 0;

  const embbData = state.metrics?.slice_metrics?.embb;
  const urllcData = state.metrics?.slice_metrics?.urllc;
  const mmtcData = state.metrics?.slice_metrics?.mmtc;

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-slate-950 via-purple-950 to-slate-900 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl animate-pulse" style={{animationDelay: '1s'}}></div>
        <div className="absolute top-1/2 right-1/3 w-64 h-64 bg-pink-600/10 rounded-full blur-3xl animate-pulse" style={{animationDelay: '2s'}}></div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 relative z-10">
        
        {/* Header */}
        <div className="mb-12 animate-fade-in">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-6">
              <div className="relative">
                <div className={`w-5 h-5 rounded-full ${state.connectionStatus === 'connected' ? 'bg-emerald-500' : 'bg-red-500'} shadow-lg`}></div>
                <div className={`absolute inset-0 w-5 h-5 rounded-full ${state.connectionStatus === 'connected' ? 'bg-emerald-500' : 'bg-red-500'} animate-ping opacity-75`}></div>
              </div>
              <div>
                <h1 className="text-6xl font-black bg-gradient-to-r from-purple-400 via-fuchsia-400 to-pink-400 bg-clip-text text-transparent tracking-tight">
                  5G Network Slice
                </h1>
                <p className="text-xl text-purple-300/80 mt-2 font-light tracking-wide">Real-time eMBB • URLLC • mMTC Monitoring</p>
              </div>
            </div>
            <div className="text-right">
              <div className={`px-6 py-3 rounded-full ${state.connectionStatus === 'connected' ? 'bg-emerald-500/20 border-2 border-emerald-500/50' : 'bg-red-500/20 border-2 border-red-500/50'} backdrop-blur-xl`}>
                <p className="text-lg font-bold ${state.connectionStatus === 'connected' ? 'text-emerald-300' : 'text-red-300'}">
                  {state.connectionStatus === 'connected' ? '● CONNECTED' : '● DISCONNECTED'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Control Panel */}
        <div className="bg-slate-900/60 backdrop-blur-2xl border-2 border-purple-500/30 rounded-3xl p-8 mb-12 shadow-2xl shadow-purple-900/50 hover:shadow-purple-700/60 transition-all duration-500">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
            <div className="space-y-3">
              <label className="block text-sm font-bold text-purple-300 uppercase tracking-wider">Traffic Volume</label>
              <input
                type="number"
                value={trafficVolume}
                onChange={(e) => setTrafficVolume(Number(e.target.value))}
                disabled={state.isRunning}
                className="w-full px-5 py-4 bg-slate-800/80 border-2 border-purple-500/40 rounded-xl text-white font-mono text-lg disabled:opacity-50 focus:outline-none focus:border-purple-400 focus:ring-4 focus:ring-purple-500/20 transition-all duration-300"
              />
            </div>
            <div className="space-y-3">
              <label className="block text-sm font-bold text-purple-300 uppercase tracking-wider">Duration (sec)</label>
              <input
                type="number"
                value={duration}
                onChange={(e) => setDuration(Number(e.target.value))}
                disabled={state.isRunning}
                className="w-full px-5 py-4 bg-slate-800/80 border-2 border-purple-500/40 rounded-xl text-white font-mono text-lg disabled:opacity-50 focus:outline-none focus:border-purple-400 focus:ring-4 focus:ring-purple-500/20 transition-all duration-300"
              />
            </div>
            <div className="space-y-3">
              <label className="block text-sm font-bold text-purple-300 uppercase tracking-wider">Pattern</label>
              <select
                value={pattern}
                onChange={(e) => setPattern(e.target.value)}
                disabled={state.isRunning}
                className="w-full px-5 py-4 bg-slate-800/80 border-2 border-purple-500/40 rounded-xl text-white text-lg disabled:opacity-50 focus:outline-none focus:border-purple-400 focus:ring-4 focus:ring-purple-500/20 transition-all duration-300 cursor-pointer"
              >
                <option value="constant">Constant</option>
                <option value="linear_increase">Linear Inc</option>
                <option value="burst">Burst</option>
                <option value="wave">Wave</option>
              </select>
            </div>
            <div className="md:col-span-2 flex items-end gap-4">
              {!state.isRunning ? (
                <button
                  onClick={startSimulation}
                  className="flex-1 bg-gradient-to-r from-emerald-500 via-green-500 to-emerald-600 hover:from-emerald-600 hover:via-green-600 hover:to-emerald-700 text-white font-black py-4 px-8 rounded-xl flex items-center justify-center gap-3 transition-all duration-300 shadow-2xl shadow-emerald-500/40 hover:shadow-emerald-500/60 hover:scale-105 active:scale-95 text-lg"
                >
                  <Play size={24} fill="white" /> START
                </button>
              ) : (
                <button
                  onClick={stopSimulation}
                  className="flex-1 bg-gradient-to-r from-red-500 via-pink-500 to-red-600 hover:from-red-600 hover:via-pink-600 hover:to-red-700 text-white font-black py-4 px-8 rounded-xl flex items-center justify-center gap-3 transition-all duration-300 shadow-2xl shadow-red-500/40 hover:shadow-red-500/60 hover:scale-105 active:scale-95 text-lg"
                >
                  <Pause size={24} fill="white" /> STOP
                </button>
              )}
              <button
                onClick={resetSimulation}
                className="bg-slate-700/80 hover:bg-slate-600 border-2 border-slate-500/50 text-white font-bold py-4 px-6 rounded-xl flex items-center justify-center gap-2 transition-all duration-300 hover:scale-105 active:scale-95 shadow-lg"
              >
                <RotateCcw size={24} />
              </button>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        {state.metrics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
            {/* Total Traffic */}
            <div className="group relative bg-gradient-to-br from-violet-600 via-purple-700 to-violet-800 rounded-2xl p-6 border-2 border-violet-400/40 shadow-2xl shadow-violet-900/50 hover:shadow-violet-600/60 transition-all duration-500 hover:scale-105 overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent"></div>
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-black text-violet-200 uppercase tracking-wider">Total Traffic</h3>
                  <Activity className="text-violet-300" size={28} />
                </div>
                <p className="text-4xl font-black text-white mb-1">{state.metrics.total_traffic_generated.toLocaleString()}</p>
                <p className="text-sm text-violet-300 font-semibold">packets generated</p>
              </div>
            </div>

            {/* Processed */}
            <div className="group relative bg-gradient-to-br from-emerald-600 via-green-700 to-emerald-800 rounded-2xl p-6 border-2 border-emerald-400/40 shadow-2xl shadow-emerald-900/50 hover:shadow-emerald-600/60 transition-all duration-500 hover:scale-105 overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent"></div>
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-black text-emerald-200 uppercase tracking-wider">Processed</h3>
                  <TrendingUp className="text-emerald-300" size={28} />
                </div>
                <p className="text-4xl font-black text-white mb-1">{state.metrics.total_packets_processed.toLocaleString()}</p>
                <p className="text-sm text-emerald-300 font-semibold">packets delivered</p>
              </div>
            </div>

            {/* Dropped */}
            <div className="group relative bg-gradient-to-br from-red-600 via-rose-700 to-red-800 rounded-2xl p-6 border-2 border-red-400/40 shadow-2xl shadow-red-900/50 hover:shadow-red-600/60 transition-all duration-500 hover:scale-105 overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent"></div>
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-black text-red-200 uppercase tracking-wider">Dropped</h3>
                  <Zap className="text-red-300" size={28} />
                </div>
                <p className="text-4xl font-black text-white mb-1">{state.metrics.total_packets_dropped.toLocaleString()}</p>
                <p className="text-sm text-red-300 font-semibold">packets lost</p>
              </div>
            </div>

            {/* Success Rate */}
            <div className="group relative bg-gradient-to-br from-cyan-600 via-blue-700 to-cyan-800 rounded-2xl p-6 border-2 border-cyan-400/40 shadow-2xl shadow-cyan-900/50 hover:shadow-cyan-600/60 transition-all duration-500 hover:scale-105 overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent"></div>
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-black text-cyan-200 uppercase tracking-wider">Success Rate</h3>
                  <Network className="text-cyan-300" size={28} />
                </div>
                <p className="text-4xl font-black text-white mb-1">{Math.round(successRate)}%</p>
                <p className="text-sm text-cyan-300 font-semibold">efficiency</p>
              </div>
            </div>
          </div>
        )}

        {/* Slice Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          
          {/* eMBB */}
          <div className="group relative bg-gradient-to-br from-blue-600 via-indigo-700 to-blue-900 rounded-3xl p-8 border-2 border-blue-400/40 shadow-2xl shadow-blue-900/60 hover:shadow-blue-600/70 transition-all duration-500 hover:scale-[1.02] overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent"></div>
            <div className="absolute top-0 right-0 w-64 h-64 bg-blue-400/10 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-700"></div>
            
            <div className="relative z-10">
              <div className="flex items-center justify-between mb-8">
                <div>
                  <h3 className="text-3xl font-black text-blue-50 tracking-tight">eMBB</h3>
                  <p className="text-sm text-blue-300 font-semibold mt-1">Enhanced Mobile Broadband</p>
                </div>
                <div className="bg-blue-500/30 p-4 rounded-2xl backdrop-blur-xl border border-blue-400/30">
                  <Radio size={36} className="text-blue-200" />
                </div>
              </div>
              
              {embbData ? (
                <div className="space-y-4">
                  <div className="bg-black/40 backdrop-blur-xl rounded-2xl p-5 border border-blue-400/30 hover:border-blue-400/60 transition-all duration-300 hover:bg-black/50">
                    <p className="text-xs text-blue-300 font-bold uppercase tracking-wider mb-2">Latency Average</p>
                    <p className="text-3xl font-black text-blue-50">{(embbData.metrics?.latency?.avg || 0).toFixed(1)} <span className="text-xl text-blue-300">ms</span></p>
                  </div>
                  <div className="bg-black/40 backdrop-blur-xl rounded-2xl p-5 border border-blue-400/30 hover:border-blue-400/60 transition-all duration-300 hover:bg-black/50">
                    <p className="text-xs text-blue-300 font-bold uppercase tracking-wider mb-2">Throughput Average</p>
                    <p className="text-3xl font-black text-blue-50">{(embbData.metrics?.throughput?.avg || 0).toFixed(0)} <span className="text-xl text-blue-300">Mbps</span></p>
                  </div>
                  <div className="bg-black/40 backdrop-blur-xl rounded-2xl p-5 border border-blue-400/30 hover:border-blue-400/60 transition-all duration-300 hover:bg-black/50">
                    <p className="text-xs text-blue-300 font-bold uppercase tracking-wider mb-2">QoS Compliance</p>
                    <p className="text-3xl font-black text-blue-50">{(embbData.qos_compliance_rate || 0).toFixed(1)}<span className="text-xl text-blue-300">%</span></p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-blue-400 border-t-transparent"></div>
                  <p className="text-blue-300 font-semibold mt-4">Waiting for data...</p>
                </div>
              )}
            </div>
          </div>

          {/* URLLC */}
          <div className="group relative bg-gradient-to-br from-red-600 via-rose-700 to-red-900 rounded-3xl p-8 border-2 border-red-400/40 shadow-2xl shadow-red-900/60 hover:shadow-red-600/70 transition-all duration-500 hover:scale-[1.02] overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent"></div>
            <div className="absolute top-0 right-0 w-64 h-64 bg-red-400/10 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-700"></div>
            
            <div className="relative z-10">
              <div className="flex items-center justify-between mb-8">
                <div>
                  <h3 className="text-3xl font-black text-red-50 tracking-tight">URLLC</h3>
                  <p className="text-sm text-red-300 font-semibold mt-1">Ultra-Reliable Low Latency</p>
                </div>
                <div className="bg-red-500/30 p-4 rounded-2xl backdrop-blur-xl border border-red-400/30">
                  <Zap size={36} className="text-red-200" />
                </div>
              </div>
              
              {urllcData ? (
                <div className="space-y-4">
                  <div className="bg-black/40 backdrop-blur-xl rounded-2xl p-5 border border-red-400/30 hover:border-red-400/60 transition-all duration-300 hover:bg-black/50">
                    <p className="text-xs text-red-300 font-bold uppercase tracking-wider mb-2">Latency Average</p>
                    <p className="text-3xl font-black text-red-50">{(urllcData.metrics?.latency?.avg || 0).toFixed(2)} <span className="text-xl text-red-300">ms</span></p>
                  </div>
                  <div className="bg-black/40 backdrop-blur-xl rounded-2xl p-5 border border-red-400/30 hover:border-red-400/60 transition-all duration-300 hover:bg-black/50">
                    <p className="text-xs text-red-300 font-bold uppercase tracking-wider mb-2">Reliability Index</p>
                    <p className="text-3xl font-black text-red-50">{(urllcData.reliability_index || 0).toFixed(2)}<span className="text-xl text-red-300">%</span></p>
                  </div>
                  <div className="bg-black/40 backdrop-blur-xl rounded-2xl p-5 border border-red-400/30 hover:border-red-400/60 transition-all duration-300 hover:bg-black/50">
                    <p className="text-xs text-red-300 font-bold uppercase tracking-wider mb-2">Packets Retransmitted</p>
                    <p className="text-3xl font-black text-red-50">{urllcData.packets_retransmitted || 0}</p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-red-400 border-t-transparent"></div>
                  <p className="text-red-300 font-semibold mt-4">Waiting for data...</p>
                </div>
              )}
            </div>
          </div>

          {/* mMTC */}
          <div className="group relative bg-gradient-to-br from-emerald-600 via-green-700 to-emerald-900 rounded-3xl p-8 border-2 border-emerald-400/40 shadow-2xl shadow-emerald-900/60 hover:shadow-emerald-600/70 transition-all duration-500 hover:scale-[1.02] overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent"></div>
            <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-400/10 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-700"></div>
            
            <div className="relative z-10">
              <div className="flex items-center justify-between mb-8">
                <div>
                  <h3 className="text-3xl font-black text-emerald-50 tracking-tight">mMTC</h3>
                  <p className="text-sm text-emerald-300 font-semibold mt-1">Massive Machine-Type Comms</p>
                </div>
                <div className="bg-emerald-500/30 p-4 rounded-2xl backdrop-blur-xl border border-emerald-400/30">
                  <Network size={36} className="text-emerald-200" />
                </div>
              </div>
              
              {mmtcData ? (
                <div className="space-y-4">
                  <div className="bg-black/40 backdrop-blur-xl rounded-2xl p-5 border border-emerald-400/30 hover:border-emerald-400/60 transition-all duration-300 hover:bg-black/50">
                    <p className="text-xs text-emerald-300 font-bold uppercase tracking-wider mb-2">Latency Average</p>
                    <p className="text-3xl font-black text-emerald-50">{(mmtcData.metrics?.latency?.avg || 0).toFixed(0)} <span className="text-xl text-emerald-300">ms</span></p>
                  </div>
                  <div className="bg-black/40 backdrop-blur-xl rounded-2xl p-5 border border-emerald-400/30 hover:border-emerald-400/60 transition-all duration-300 hover:bg-black/50">
                    <p className="text-xs text-emerald-300 font-bold uppercase tracking-wider mb-2">Active Devices</p>
                    <p className="text-3xl font-black text-emerald-50">{mmtcData.active_devices || 0}</p>
                  </div>
                  <div className="bg-black/40 backdrop-blur-xl rounded-2xl p-5 border border-emerald-400/30 hover:border-emerald-400/60 transition-all duration-300 hover:bg-black/50">
                    <p className="text-xs text-emerald-300 font-bold uppercase tracking-wider mb-2">Success Rate</p>
                    <p className="text-3xl font-black text-emerald-50">{(mmtcData.success_rate || 0).toFixed(1)}<span className="text-xl text-emerald-300">%</span></p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-emerald-400 border-t-transparent"></div>
                  <p className="text-emerald-300 font-semibold mt-4">Waiting for data...</p>
                </div>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}