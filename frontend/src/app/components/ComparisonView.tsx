'use client';

import React, { useState, useEffect } from 'react';

interface SimulationData {
  simulation_id: string;
  traffic_volume: number;
  duration: number;
  pattern: string;
  total_packets_processed: number;
  total_packets_dropped: number;
  total_traffic_generated: number;
}

interface ComparisonViewProps {
  onClose?: () => void;
}

export default function ComparisonView({ onClose }: ComparisonViewProps) {
  const [simulations, setSimulations] = useState<SimulationData[]>([]);
  const [sim1, setSim1] = useState<string>('');
  const [sim2, setSim2] = useState<string>('');
  const [sim1Data, setSim1Data] = useState<SimulationData | null>(null);
  const [sim2Data, setSim2Data] = useState<SimulationData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchSimulations();
  }, []);

  const fetchSimulations = async () => {
    try {
      const res = await fetch('http://localhost:8000/simulations/history?limit=100');
      const data = await res.json();
      setSimulations(data.simulations || []);
    } catch (error) {
      console.error('Error fetching simulations:', error);
    }
  };

  const fetchSimulationData = async (simId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/simulation/${simId}`);
      return await res.json();
    } catch (error) {
      console.error('Error fetching simulation:', error);
      return null;
    }
  };

  const handleCompare = async () => {
    if (!sim1 || !sim2) {
      alert('Please select two simulations');
      return;
    }

    setLoading(true);
    const data1 = await fetchSimulationData(sim1);
    const data2 = await fetchSimulationData(sim2);
    setSim1Data(data1);
    setSim2Data(data2);
    setLoading(false);
  };

  const calculateSuccessRate = (data: SimulationData) => {
    return data.total_traffic_generated > 0
      ? ((data.total_packets_processed - data.total_packets_dropped) / data.total_traffic_generated) * 100
      : 0;
  };

  const getComparison = (key: keyof SimulationData, label: string) => {
    if (!sim1Data || !sim2Data) return null;

    const val1 = sim1Data[key];
    const val2 = sim2Data[key];
    const difference = typeof val1 === 'number' && typeof val2 === 'number' ? val1 - val2 : 0;
    const isHigherBetter = key === 'total_packets_processed';
    const winner = difference > 0 ? isHigherBetter ? 'sim1' : 'sim2' : difference < 0 ? isHigherBetter ? 'sim2' : 'sim1' : 'tie';

    return (
      <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700">
        <h3 className="text-sm font-bold text-purple-300 mb-3">{label}</h3>
        <div className="grid grid-cols-3 gap-4">
          <div className={`p-3 rounded-lg ${winner === 'sim1' ? 'bg-emerald-500/20 border-2 border-emerald-500/50' : 'bg-slate-700/50'}`}>
            <p className="text-xs text-slate-400 mb-1">Sim 1</p>
            <p className={`text-lg font-bold ${winner === 'sim1' ? 'text-emerald-400' : 'text-slate-300'}`}>
              {typeof val1 === 'number' ? val1.toLocaleString() : val1}
            </p>
          </div>
          <div className="p-3 rounded-lg bg-slate-700/50 flex items-center justify-center">
            <p className="text-sm font-bold text-slate-400">
              {difference > 0 ? '+' : ''}{difference.toLocaleString()}
            </p>
          </div>
          <div className={`p-3 rounded-lg ${winner === 'sim2' ? 'bg-emerald-500/20 border-2 border-emerald-500/50' : 'bg-slate-700/50'}`}>
            <p className="text-xs text-slate-400 mb-1">Sim 2</p>
            <p className={`text-lg font-bold ${winner === 'sim2' ? 'text-emerald-400' : 'text-slate-300'}`}>
              {typeof val2 === 'number' ? val2.toLocaleString() : val2}
            </p>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Selection */}
      <div className="card bg-slate-900/60 border-purple-500/30">
        <h2 className="text-2xl font-bold text-purple-400 mb-6">Compare Simulations</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div>
            <label className="block text-sm font-bold text-purple-300 mb-2">Simulation 1</label>
            <select
              value={sim1}
              onChange={(e) => setSim1(e.target.value)}
              className="select-field"
            >
              <option value="">Select simulation</option>
              {simulations.map((s) => (
                <option key={s.simulation_id} value={s.simulation_id}>
                  {s.simulation_id} ({s.pattern})
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end justify-center">
            <button
              onClick={handleCompare}
              disabled={loading}
              className="btn-primary w-full disabled:opacity-50"
            >
              {loading ? 'Comparing...' : 'Compare'}
            </button>
          </div>

          <div>
            <label className="block text-sm font-bold text-purple-300 mb-2">Simulation 2</label>
            <select
              value={sim2}
              onChange={(e) => setSim2(e.target.value)}
              className="select-field"
            >
              <option value="">Select simulation</option>
              {simulations.map((s) => (
                <option key={s.simulation_id} value={s.simulation_id}>
                  {s.simulation_id} ({s.pattern})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Comparison Results */}
      {sim1Data && sim2Data && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {getComparison('total_packets_processed', 'Packets Processed')}
            {getComparison('total_packets_dropped', 'Packets Dropped')}
          </div>

          <div className="card bg-slate-900/60 border-purple-500/30">
            <h3 className="text-lg font-bold text-purple-400 mb-4">Success Rate Comparison</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-slate-800/50 p-4 rounded-lg">
                <p className="text-sm text-slate-400 mb-2">Sim 1 Rate</p>
                <p className="text-3xl font-bold text-blue-400">{calculateSuccessRate(sim1Data).toFixed(2)}%</p>
              </div>
              <div className="bg-slate-800/50 p-4 rounded-lg flex items-center justify-center">
                <p className="text-lg font-bold text-slate-400">
                  Δ {(calculateSuccessRate(sim1Data) - calculateSuccessRate(sim2Data)).toFixed(2)}%
                </p>
              </div>
              <div className="bg-slate-800/50 p-4 rounded-lg">
                <p className="text-sm text-slate-400 mb-2">Sim 2 Rate</p>
                <p className="text-3xl font-bold text-blue-400">{calculateSuccessRate(sim2Data).toFixed(2)}%</p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card bg-slate-900/60 border-purple-500/30">
              <h3 className="text-lg font-bold text-purple-400 mb-4">Configuration 1</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-400">Traffic Volume:</span>
                  <span className="text-white font-semibold">{sim1Data.traffic_volume.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Duration:</span>
                  <span className="text-white font-semibold">{sim1Data.duration}s</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Pattern:</span>
                  <span className="text-white font-semibold capitalize">{sim1Data.pattern}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Total Generated:</span>
                  <span className="text-white font-semibold">{sim1Data.total_traffic_generated.toLocaleString()}</span>
                </div>
              </div>
            </div>

            <div className="card bg-slate-900/60 border-purple-500/30">
              <h3 className="text-lg font-bold text-purple-400 mb-4">Configuration 2</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-400">Traffic Volume:</span>
                  <span className="text-white font-semibold">{sim2Data.traffic_volume.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Duration:</span>
                  <span className="text-white font-semibold">{sim2Data.duration}s</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Pattern:</span>
                  <span className="text-white font-semibold capitalize">{sim2Data.pattern}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Total Generated:</span>
                  <span className="text-white font-semibold">{sim2Data.total_traffic_generated.toLocaleString()}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}