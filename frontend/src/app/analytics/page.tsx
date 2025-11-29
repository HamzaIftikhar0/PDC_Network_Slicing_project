'use client';

import React, { useState, useEffect } from 'react';
import Charts from '../components/Charts';
import ExportButtons from '../components/ExportButtons';

interface MetricsData {
  timestamp: string;
  total_traffic_generated: number;
  total_packets_processed: number;
  total_packets_dropped: number;
  slice_metrics: Record<string, any>;
}

export default function DashboardPage() {
  const [metricsHistory, setMetricsHistory] = useState<MetricsData[]>([]);
  const [simulationId, setSimulationId] = useState<string | null>(null);

  useEffect(() => {
    // Fetch metrics from localStorage or API
    const savedHistory = localStorage.getItem('metricsHistory');
    const savedSimId = localStorage.getItem('currentSimulationId');

    if (savedHistory) {
      setMetricsHistory(JSON.parse(savedHistory));
    }
    if (savedSimId) {
      setSimulationId(savedSimId);
    }
  }, []);

  const calculateStats = () => {
    if (metricsHistory.length === 0) {
      return {
        avgSuccessRate: 0,
        totalPacketsProcessed: 0,
        totalPacketsDropped: 0,
        peakTraffic: 0,
      };
    }

    const lastMetric = metricsHistory[metricsHistory.length - 1];
    const avgSuccessRate = metricsHistory.reduce((sum, m) => {
      const rate = m.total_traffic_generated > 0
        ? ((m.total_packets_processed - m.total_packets_dropped) / m.total_traffic_generated) * 100
        : 0;
      return sum + rate;
    }, 0) / metricsHistory.length;

    return {
      avgSuccessRate: avgSuccessRate.toFixed(2),
      totalPacketsProcessed: lastMetric.total_packets_processed.toLocaleString(),
      totalPacketsDropped: lastMetric.total_packets_dropped.toLocaleString(),
      peakTraffic: Math.max(...metricsHistory.map(m => m.total_traffic_generated)).toLocaleString(),
    };
  };

  const stats = calculateStats();

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="animate-fade-in">
        <h1 className="text-4xl font-black text-purple-400 mb-2">Analytics Dashboard</h1>
        <p className="text-slate-400">Real-time metrics and performance visualization</p>
      </div>

      {/* Statistics Cards */}
      {metricsHistory.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="stat-card bg-gradient-to-br from-purple-600 to-purple-800 border-purple-400/40">
            <div className="relative z-10">
              <p className="text-sm font-bold text-purple-200 uppercase mb-2">Average Success Rate</p>
              <p className="text-4xl font-black text-white">{stats.avgSuccessRate}%</p>
            </div>
          </div>

          <div className="stat-card bg-gradient-to-br from-blue-600 to-blue-800 border-blue-400/40">
            <div className="relative z-10">
              <p className="text-sm font-bold text-blue-200 uppercase mb-2">Total Processed</p>
              <p className="text-4xl font-black text-white">{stats.totalPacketsProcessed}</p>
            </div>
          </div>

          <div className="stat-card bg-gradient-to-br from-red-600 to-red-800 border-red-400/40">
            <div className="relative z-10">
              <p className="text-sm font-bold text-red-200 uppercase mb-2">Total Dropped</p>
              <p className="text-4xl font-black text-white">{stats.totalPacketsDropped}</p>
            </div>
          </div>

          <div className="stat-card bg-gradient-to-br from-cyan-600 to-cyan-800 border-cyan-400/40">
            <div className="relative z-10">
              <p className="text-sm font-bold text-cyan-200 uppercase mb-2">Peak Traffic</p>
              <p className="text-4xl font-black text-white">{stats.peakTraffic}</p>
            </div>
          </div>
        </div>
      )}

      {/* Export Buttons */}
      <div className="card bg-slate-900/60 border-purple-500/30">
        <h2 className="text-2xl font-bold text-purple-400 mb-4">Export Options</h2>
        <ExportButtons
          simulationId={simulationId}
          metricsHistory={metricsHistory}
          isEnabled={metricsHistory.length > 0}
        />
      </div>

      {/* Charts */}
      <div className="card bg-slate-900/60 border-purple-500/30">
        <h2 className="text-2xl font-bold text-purple-400 mb-6">Performance Charts</h2>
        <Charts metricsHistory={metricsHistory} />
      </div>

      {/* Empty State */}
      {metricsHistory.length === 0 && (
        <div className="card bg-slate-900/60 border-purple-500/30 text-center py-12">
          <p className="text-slate-400 text-lg">No data available yet</p>
          <p className="text-slate-500 mt-2">Go to the main dashboard and start a simulation to see analytics</p>
        </div>
      )}
    </div>
  );
}