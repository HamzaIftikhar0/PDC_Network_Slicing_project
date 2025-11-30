'use client';

import React, { useState, useEffect } from 'react';
import SimulationHistory from '../components/SimulationHistory';

export default function HistoryPage() {
  const [isOffline, setIsOffline] = useState(false);
  const [alertVisible, setAlertVisible] = useState(true);

  useEffect(() => {
    // Check initial connectivity
    setIsOffline(!navigator.onLine);

    // Listen for online/offline events
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const handleSelectSimulation = (simId: string) => {
    console.log('Selected simulation:', simId);
    
    if (isOffline) {
      console.warn('Offline: Cannot fetch simulation details');
      alert('Cannot fetch simulation details while offline. Please check your connection.');
      return;
    }

    // Fetch simulation details
    fetch(`http://localhost:8000/simulation/${simId}`)
      .then(res => res.json())
      .then(data => {
        console.log('Simulation details:', data);
        localStorage.setItem('selectedSimulation', JSON.stringify(data));
      })
      .catch(error => console.error('Error fetching simulation:', error));
  };

  return (
    <div className="space-y-8">
      {/* Service Status Alert - ADD THIS */}
      {isOffline && alertVisible && (
        <div className="animate-fade-in rounded-lg border border-red-500/50 bg-red-900/30 p-4 flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <span className="text-red-400 text-xl mt-0.5">⚠️</span>
            <div>
              <h3 className="font-semibold text-red-300 mb-1">Service Status: Offline</h3>
              <p className="text-sm text-red-200/80">
                You are currently offline. Some features like fetching simulation details may not work. Please check your internet connection.
              </p>
            </div>
          </div>
          <button
            onClick={() => setAlertVisible(false)}
            className="text-red-300 hover:text-red-200 transition-colors flex-shrink-0"
            aria-label="Dismiss alert"
          >
            ✕
          </button>
        </div>
      )}

      {/* Header */}
      <div className="animate-fade-in">
        <h1 className="text-4xl font-black text-purple-400 mb-2">Simulation History</h1>
        <p className="text-slate-400">View, filter, export, and manage all your simulations</p>
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card bg-gradient-to-br from-blue-600/20 to-blue-800/20 border-blue-400/40">
          <div className="relative z-10">
            <p className="text-sm font-bold text-blue-300 uppercase mb-2">📊 View</p>
            <p className="text-slate-300">Browse all your simulation runs with detailed metrics</p>
          </div>
        </div>

        <div className="card bg-gradient-to-br from-emerald-600/20 to-emerald-800/20 border-emerald-400/40">
          <div className="relative z-10">
            <p className="text-sm font-bold text-emerald-300 uppercase mb-2">💾 Export</p>
            <p className="text-slate-300">Download simulation data in CSV or JSON format</p>
          </div>
        </div>

        <div className="card bg-gradient-to-br from-red-600/20 to-red-800/20 border-red-400/40">
          <div className="relative z-10">
            <p className="text-sm font-bold text-red-300 uppercase mb-2">🗑️ Delete</p>
            <p className="text-slate-300">Remove old simulations to keep your history clean</p>
          </div>
        </div>
      </div>

      {/* Simulation History Table */}
      <div className="card bg-slate-900/60 border-purple-500/30">
        <h2 className="text-2xl font-bold text-purple-400 mb-6">All Simulations</h2>
        <SimulationHistory onSelectSimulation={handleSelectSimulation} />
      </div>

      {/* Tips Section */}
      <div className="card bg-slate-900/60 border-purple-500/30">
        <h3 className="text-xl font-bold text-purple-400 mb-4">💡 Tips</h3>
        <ul className="space-y-3 text-slate-300">
          <li className="flex gap-3">
            <span className="text-purple-400">•</span>
            <span>Use filters to quickly find specific simulations by status</span>
          </li>
          <li className="flex gap-3">
            <span className="text-purple-400">•</span>
            <span>Export data to analyze in Excel or your preferred tool</span>
          </li>
          <li className="flex gap-3">
            <span className="text-purple-400">•</span>
            <span>Click the eye icon to view detailed metrics for a simulation</span>
          </li>
          <li className="flex gap-3">
            <span className="text-purple-400">•</span>
            <span>Use the trash icon to delete simulations you no longer need</span>
          </li>
        </ul>
      </div>
    </div>
  );
}