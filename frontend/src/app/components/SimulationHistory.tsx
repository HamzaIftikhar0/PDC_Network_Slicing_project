'use client';

import React, { useState, useEffect } from 'react';
import { Trash2, Eye, Download } from 'lucide-react';

interface Simulation {
  id: number;
  simulation_id: string;
  traffic_volume: number;
  duration: number;
  pattern: string;
  status: string;
  total_traffic_generated: number;
  total_packets_processed: number;
  total_packets_dropped: number;
  start_time: string;
  end_time: string;
  created_at: string;
}

interface SimulationHistoryProps {
  onSelectSimulation?: (simId: string) => void;
}

export default function SimulationHistory({ onSelectSimulation }: SimulationHistoryProps) {
  const [simulations, setSimulations] = useState<Simulation[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<'all' | 'completed' | 'running' | 'failed'>('all');

  useEffect(() => {
    fetchSimulations();
  }, [filter]);

  const fetchSimulations = async () => {
    setLoading(true);
    try {
      const url = filter === 'all' 
        ? 'http://localhost:8000/simulations/history' 
        : `http://localhost:8000/simulations/history?status=${filter}`;
      
      const res = await fetch(url);
      const data = await res.json();
      setSimulations(data.simulations || []);
    } catch (error) {
      console.error('Error fetching simulations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (simId: string) => {
    if (confirm('Delete this simulation?')) {
      try {
        await fetch(`http://localhost:8000/simulation/${simId}`, {
          method: 'DELETE',
        });
        fetchSimulations();
      } catch (error) {
        console.error('Error deleting simulation:', error);
      }
    }
  };

  const handleExport = async (simId: string, format: 'csv' | 'json') => {
    try {
      const res = await fetch('http://localhost:8000/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          simulation_id: simId,
          format,
          include_metrics: true,
          include_slice_metrics: true,
        }),
      });
      const data = await res.json();
      if (data.success) {
        alert(`Exported: ${data.file_name}`);
      }
    } catch (error) {
      console.error('Error exporting:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Filter */}
      <div className="flex gap-4 flex-wrap">
        {(['all', 'completed', 'running', 'failed'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded-lg font-semibold capitalize smooth-transition ${
              filter === f
                ? 'bg-purple-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b-2 border-purple-500/30">
              <th className="px-6 py-4 text-left text-sm font-bold text-purple-300">Simulation ID</th>
              <th className="px-6 py-4 text-left text-sm font-bold text-purple-300">Pattern</th>
              <th className="px-6 py-4 text-left text-sm font-bold text-purple-300">Duration</th>
              <th className="px-6 py-4 text-left text-sm font-bold text-purple-300">Status</th>
              <th className="px-6 py-4 text-left text-sm font-bold text-purple-300">Processed</th>
              <th className="px-6 py-4 text-left text-sm font-bold text-purple-300">Dropped</th>
              <th className="px-6 py-4 text-left text-sm font-bold text-purple-300">Success Rate</th>
              <th className="px-6 py-4 text-left text-sm font-bold text-purple-300">Created</th>
              <th className="px-6 py-4 text-left text-sm font-bold text-purple-300">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={9} className="px-6 py-8 text-center">
                  <div className="flex items-center justify-center gap-2">
                    <div className="animate-spin rounded-full h-6 w-6 border-2 border-purple-400 border-t-transparent"></div>
                    <span className="text-slate-400">Loading...</span>
                  </div>
                </td>
              </tr>
            ) : simulations.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-6 py-8 text-center text-slate-400">
                  No simulations found
                </td>
              </tr>
            ) : (
              simulations.map((sim) => {
                const successRate = sim.total_traffic_generated > 0
                  ? ((sim.total_packets_processed - sim.total_packets_dropped) / sim.total_traffic_generated) * 100
                  : 0;
                
                return (
                  <tr key={sim.id} className="border-b border-slate-700/50 hover:bg-slate-800/50 smooth-transition">
                    <td className="px-6 py-4 text-sm text-slate-300 font-mono">{sim.simulation_id}</td>
                    <td className="px-6 py-4 text-sm text-slate-300 capitalize">{sim.pattern}</td>
                    <td className="px-6 py-4 text-sm text-slate-300">{sim.duration}s</td>
                    <td className="px-6 py-4 text-sm">
                      <span className={`px-3 py-1 rounded-full text-xs font-bold capitalize ${
                        sim.status === 'completed' ? 'bg-emerald-500/20 text-emerald-300' :
                        sim.status === 'running' ? 'bg-blue-500/20 text-blue-300' :
                        sim.status === 'failed' ? 'bg-red-500/20 text-red-300' :
                        'bg-slate-500/20 text-slate-300'
                      }`}>
                        {sim.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-300">{sim.total_packets_processed.toLocaleString()}</td>
                    <td className="px-6 py-4 text-sm text-slate-300">{sim.total_packets_dropped.toLocaleString()}</td>
                    <td className="px-6 py-4 text-sm text-slate-300">{successRate.toFixed(2)}%</td>
                    <td className="px-6 py-4 text-sm text-slate-300">{new Date(sim.created_at).toLocaleDateString()}</td>
                    <td className="px-6 py-4 text-sm">
                      <div className="flex gap-2">
                        <button
                          onClick={() => onSelectSimulation?.(sim.simulation_id)}
                          className="p-2 hover:bg-slate-700 rounded-lg smooth-transition"
                          title="View"
                        >
                          <Eye size={16} className="text-blue-400" />
                        </button>
                        <button
                          onClick={() => handleExport(sim.simulation_id, 'csv')}
                          className="p-2 hover:bg-slate-700 rounded-lg smooth-transition"
                          title="Export CSV"
                        >
                          <Download size={16} className="text-green-400" />
                        </button>
                        <button
                          onClick={() => handleDelete(sim.simulation_id)}
                          className="p-2 hover:bg-slate-700 rounded-lg smooth-transition"
                          title="Delete"
                        >
                          <Trash2 size={16} className="text-red-400" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}