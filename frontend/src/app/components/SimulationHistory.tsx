"use client";

import React, { useState, useEffect } from "react";

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

export default function SimulationHistory({
  onSelectSimulation,
}: SimulationHistoryProps) {
  const [simulations, setSimulations] = useState<Simulation[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<
    "all" | "completed" | "running" | "failed"
  >("all");
  const [serviceHealth, setServiceHealth] = useState({
    backend: false,
    scheduler: false,
    embb: false,
    urllc: false,
    mmtc: false,
  });

  useEffect(() => {
    checkServiceHealth();
    const interval = setInterval(checkServiceHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const checkServiceHealth = async () => {
    const services = [
      { name: "backend", url: "http://localhost:8000/health" },
      { name: "scheduler", url: "http://localhost:8001/health" },
      { name: "embb", url: "http://localhost:8101/health" },
      { name: "urllc", url: "http://localhost:8102/health" },
      { name: "mmtc", url: "http://localhost:8103/health" },
    ];

    const health: any = {};

    await Promise.all(
      services.map(async (service) => {
        try {
          const res = await fetch(service.url, {
            signal: AbortSignal.timeout(3000),
          });
          health[service.name] = res.ok;
        } catch {
          health[service.name] = false;
        }
      })
    );

    setServiceHealth(health);
  };

  useEffect(() => {
    fetchSimulations();
  }, [filter]);

  const fetchSimulations = async () => {
    setLoading(true);
    try {
      const url =
        filter === "all"
          ? "http://localhost:8000/simulations/history"
          : `http://localhost:8000/simulations/history?status=${filter}`;

      const res = await fetch(url);
      const data = await res.json();
      setSimulations(data.simulations || []);
    } catch (error) {
      console.error("Error fetching simulations:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (simId: string) => {
    if (confirm("Delete this simulation?")) {
      try {
        await fetch(`http://localhost:8000/simulation/${simId}`, {
          method: "DELETE",
        });
        fetchSimulations();
      } catch (error) {
        console.error("Error deleting simulation:", error);
      }
    }
  };

  const handleExport = async (simId: string, format: "csv" | "json") => {
    try {
      const res = await fetch("http://localhost:8000/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
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
      console.error("Error exporting:", error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Service Health Indicators */}
      <div className="card bg-slate-900/60 border-purple-500/30">
        <h3 className="text-lg font-bold text-purple-400 mb-4">
          Service Health Status
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {Object.entries(serviceHealth).map(([service, isHealthy]) => (
            <div
              key={service}
              className={`p-4 rounded-lg border-2 ${
                isHealthy
                  ? "bg-emerald-500/20 border-emerald-500/50"
                  : "bg-red-500/20 border-red-500/50"
              }`}
            >
              <div className="flex items-center gap-2 mb-2">
                <div
                  className={`w-3 h-3 rounded-full ${
                    isHealthy ? "bg-emerald-500" : "bg-red-500"
                  }`}
                ></div>
                <span className="text-sm font-bold text-slate-200 capitalize">
                  {service}
                </span>
              </div>
              <span
                className={`text-xs font-semibold ${
                  isHealthy ? "text-emerald-300" : "text-red-300"
                }`}
              >
                {isHealthy ? "Online" : "Offline"}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Filter */}
      <div className="flex gap-4 flex-wrap">
        {(["all", "completed", "running", "failed"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded-lg font-semibold capitalize smooth-transition ${
              filter === f
                ? "bg-purple-600 text-white"
                : "bg-slate-700 text-slate-300 hover:bg-slate-600"
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
              <th className="px-6 py-4 text-left text-sm font-bold text-purple-300">
                Simulation ID
              </th>
              <th className="px-6 py-4 text-left text-sm font-bold text-purple-300">
                Pattern
              </th>
              <th className="px-6 py-4 text-left text-sm font-bold text-purple-300">
                Duration
              </th>
              <th className="px-6 py-4 text-left text-sm font-bold text-purple-300">
                Status
              </th>
              <th className="px-6 py-4 text-left text-sm font-bold text-purple-300">
                Processed
              </th>
              <th className="px-6 py-4 text-left text-sm font-bold text-purple-300">
                Dropped
              </th>
              <th className="px-6 py-4 text-left text-sm font-bold text-purple-300">
                Success Rate
              </th>
              <th className="px-6 py-4 text-left text-sm font-bold text-purple-300">
                Created
              </th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={8} className="px-6 py-8 text-center">
                  <div className="flex items-center justify-center gap-2">
                    <div className="animate-spin rounded-full h-6 w-6 border-2 border-purple-400 border-t-transparent"></div>
                    <span className="text-slate-400">Loading...</span>
                  </div>
                </td>
              </tr>
            ) : simulations.length === 0 ? (
              <tr>
                <td
                  colSpan={8}
                  className="px-6 py-8 text-center text-slate-400"
                >
                  No simulations found
                </td>
              </tr>
            ) : (
              simulations.map((sim) => {
                const successRate =
                  sim.total_traffic_generated > 0
                    ? ((sim.total_packets_processed -
                        sim.total_packets_dropped) /
                        sim.total_traffic_generated) *
                      100
                    : 0;

                return (
                  <tr
                    key={sim.id}
                    className="border-b border-slate-700/50 hover:bg-slate-800/50 smooth-transition"
                  >
                    <td className="px-6 py-4 text-sm text-slate-300 font-mono">
                      {sim.simulation_id}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-300 capitalize">
                      {sim.pattern}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-300">
                      {sim.duration}s
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-bold capitalize ${
                          sim.status === "completed"
                            ? "bg-emerald-500/20 text-emerald-300"
                            : sim.status === "running"
                            ? "bg-blue-500/20 text-blue-300"
                            : sim.status === "failed"
                            ? "bg-red-500/20 text-red-300"
                            : "bg-slate-500/20 text-slate-300"
                        }`}
                      >
                        {sim.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-300">
                      {sim.total_packets_processed.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-300">
                      {sim.total_packets_dropped.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-300">
                      {successRate.toFixed(2)}%
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-300">
                      {new Date(sim.created_at).toLocaleDateString()}
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