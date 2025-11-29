'use client';

import React from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';

interface ChartsProps {
  metricsHistory: Array<{
    timestamp: string;
    total_traffic_generated: number;
    total_packets_processed: number;
    total_packets_dropped: number;
    slice_metrics?: Record<string, any>;
  }>;
}

export default function Charts({ metricsHistory }: ChartsProps) {
  if (metricsHistory.length === 0) {
    return (
      <div className="text-center py-12 text-slate-400">
        <p>No data to display. Start a simulation to see charts.</p>
      </div>
    );
  }

  // Prepare data for charts
  const chartData = metricsHistory.map((metric, idx) => ({
    time: idx,
    traffic: metric.total_traffic_generated,
    processed: metric.total_packets_processed,
    dropped: metric.total_packets_dropped,
    successRate: metric.total_traffic_generated > 0 
      ? ((metric.total_packets_processed - metric.total_packets_dropped) / metric.total_traffic_generated) * 100
      : 0,
  }));

  // Slice-specific data
  const sliceData = metricsHistory.map((metric, idx) => ({
    time: idx,
    embb_latency: metric.slice_metrics?.embb?.metrics?.latency?.avg || 0,
    urllc_latency: metric.slice_metrics?.urllc?.metrics?.latency?.avg || 0,
    mmtc_latency: metric.slice_metrics?.mmtc?.metrics?.latency?.avg || 0,
  }));

  const sliceDropData = metricsHistory.map((metric, idx) => ({
    time: idx,
    embb_drop: metric.slice_metrics?.embb?.metrics?.drop_rate?.avg || 0,
    urllc_drop: metric.slice_metrics?.urllc?.metrics?.drop_rate?.avg || 0,
    mmtc_drop: metric.slice_metrics?.mmtc?.metrics?.drop_rate?.avg || 0,
  }));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Packets Over Time */}
      <div className="card bg-slate-900/60 border-purple-500/30">
        <h3 className="text-xl font-bold text-purple-300 mb-4">Packets Over Time</h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorProcessed" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorDropped" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
            <XAxis dataKey="time" stroke="rgba(148, 163, 184, 0.5)" />
            <YAxis stroke="rgba(148, 163, 184, 0.5)" />
            <Tooltip 
              contentStyle={{ background: '#1e293b', border: '1px solid rgba(168, 85, 247, 0.3)' }}
              labelStyle={{ color: '#f1f5f9' }}
            />
            <Legend />
            <Area type="monotone" dataKey="processed" stroke="#10b981" fillOpacity={1} fill="url(#colorProcessed)" name="Processed" />
            <Area type="monotone" dataKey="dropped" stroke="#ef4444" fillOpacity={1} fill="url(#colorDropped)" name="Dropped" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Success Rate */}
      <div className="card bg-slate-900/60 border-purple-500/30">
        <h3 className="text-xl font-bold text-purple-300 mb-4">Success Rate Over Time</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
            <XAxis dataKey="time" stroke="rgba(148, 163, 184, 0.5)" />
            <YAxis stroke="rgba(148, 163, 184, 0.5)" domain={[0, 100]} />
            <Tooltip 
              contentStyle={{ background: '#1e293b', border: '1px solid rgba(168, 85, 247, 0.3)' }}
              labelStyle={{ color: '#f1f5f9' }}
              formatter={(value) => `${(value as number).toFixed(2)}%`}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="successRate" 
              stroke="#06b6d4" 
              dot={false}
              strokeWidth={3}
              name="Success Rate %"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Slice Latencies */}
      <div className="card bg-slate-900/60 border-purple-500/30">
        <h3 className="text-xl font-bold text-purple-300 mb-4">Slice Latencies</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={sliceData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
            <XAxis dataKey="time" stroke="rgba(148, 163, 184, 0.5)" />
            <YAxis stroke="rgba(148, 163, 184, 0.5)" />
            <Tooltip 
              contentStyle={{ background: '#1e293b', border: '1px solid rgba(168, 85, 247, 0.3)' }}
              labelStyle={{ color: '#f1f5f9' }}
              formatter={(value) => `${(value as number).toFixed(2)} ms`}
            />
            <Legend />
            <Line type="monotone" dataKey="embb_latency" stroke="#3b82f6" dot={false} strokeWidth={2} name="eMBB" />
            <Line type="monotone" dataKey="urllc_latency" stroke="#ef4444" dot={false} strokeWidth={2} name="URLLC" />
            <Line type="monotone" dataKey="mmtc_latency" stroke="#10b981" dot={false} strokeWidth={2} name="mMTC" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Slice Drop Rates */}
      <div className="card bg-slate-900/60 border-purple-500/30">
        <h3 className="text-xl font-bold text-purple-300 mb-4">Slice Drop Rates</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={sliceDropData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
            <XAxis dataKey="time" stroke="rgba(148, 163, 184, 0.5)" />
            <YAxis stroke="rgba(148, 163, 184, 0.5)" />
            <Tooltip 
              contentStyle={{ background: '#1e293b', border: '1px solid rgba(168, 85, 247, 0.3)' }}
              labelStyle={{ color: '#f1f5f9' }}
              formatter={(value) => `${(value as number).toFixed(3)}%`}
            />
            <Legend />
            <Bar dataKey="embb_drop" fill="#3b82f6" name="eMBB" />
            <Bar dataKey="urllc_drop" fill="#ef4444" name="URLLC" />
            <Bar dataKey="mmtc_drop" fill="#10b981" name="mMTC" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Traffic Distribution */}
      <div className="card bg-slate-900/60 border-purple-500/30">
        <h3 className="text-xl font-bold text-purple-300 mb-4">Traffic Generation</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
            <XAxis dataKey="time" stroke="rgba(148, 163, 184, 0.5)" />
            <YAxis stroke="rgba(148, 163, 184, 0.5)" />
            <Tooltip 
              contentStyle={{ background: '#1e293b', border: '1px solid rgba(168, 85, 247, 0.3)' }}
              labelStyle={{ color: '#f1f5f9' }}
            />
            <Legend />
            <Bar dataKey="traffic" fill="#a78bfa" name="Generated Traffic" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Packet Processing Rate */}
      <div className="card bg-slate-900/60 border-purple-500/30">
        <h3 className="text-xl font-bold text-purple-300 mb-4">Processing vs Dropping</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
            <XAxis dataKey="time" stroke="rgba(148, 163, 184, 0.5)" />
            <YAxis stroke="rgba(148, 163, 184, 0.5)" />
            <Tooltip 
              contentStyle={{ background: '#1e293b', border: '1px solid rgba(168, 85, 247, 0.3)' }}
              labelStyle={{ color: '#f1f5f9' }}
            />
            <Legend />
            <Bar dataKey="processed" fill="#10b981" name="Processed" />
            <Bar dataKey="dropped" fill="#ef4444" name="Dropped" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}