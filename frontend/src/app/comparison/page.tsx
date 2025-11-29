'use client';

import React from 'react';
import ComparisonView from '../components/ComparisonView';

export default function ComparisonPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="animate-fade-in">
        <h1 className="text-4xl font-black text-purple-400 mb-2">Compare Simulations</h1>
        <p className="text-slate-400">Analyze and compare metrics from two different simulation runs</p>
      </div>

      {/* Feature Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card bg-gradient-to-br from-purple-600/20 to-purple-800/20 border-purple-400/40">
          <div className="relative z-10">
            <h3 className="text-lg font-bold text-purple-300 mb-3">🔍 Side-by-Side Analysis</h3>
            <ul className="space-y-2 text-sm text-slate-300">
              <li>• Compare any two simulations</li>
              <li>• View metrics in parallel</li>
              <li>• Identify performance differences</li>
              <li>• Highlight winning configuration</li>
            </ul>
          </div>
        </div>

        <div className="card bg-gradient-to-br from-cyan-600/20 to-cyan-800/20 border-cyan-400/40">
          <div className="relative z-10">
            <h3 className="text-lg font-bold text-cyan-300 mb-3">📊 Key Metrics</h3>
            <ul className="space-y-2 text-sm text-slate-300">
              <li>• Packets processed & dropped</li>
              <li>• Success rates</li>
              <li>• Configuration details</li>
              <li>• Performance deltas</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Comparison Tool */}
      <div className="card bg-slate-900/60 border-purple-500/30">
        <ComparisonView />
      </div>

      {/* Usage Guide */}
      <div className="card bg-slate-900/60 border-purple-500/30">
        <h3 className="text-xl font-bold text-purple-400 mb-6">How to Compare</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-3">
            <div className="bg-purple-500/20 border-2 border-purple-500/50 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-purple-400">1</p>
            </div>
            <h4 className="font-bold text-slate-300">Select First Simulation</h4>
            <p className="text-sm text-slate-400">Choose the first simulation from the dropdown menu</p>
          </div>

          <div className="space-y-3">
            <div className="bg-purple-500/20 border-2 border-purple-500/50 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-purple-400">2</p>
            </div>
            <h4 className="font-bold text-slate-300">Select Second Simulation</h4>
            <p className="text-sm text-slate-400">Choose a different simulation for comparison</p>
          </div>

          <div className="space-y-3">
            <div className="bg-purple-500/20 border-2 border-purple-500/50 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-purple-400">3</p>
            </div>
            <h4 className="font-bold text-slate-300">Click Compare</h4>
            <p className="text-sm text-slate-400">View detailed side-by-side metrics and analysis</p>
          </div>
        </div>
      </div>

      {/* Use Cases */}
      <div className="card bg-slate-900/60 border-purple-500/30">
        <h3 className="text-xl font-bold text-purple-400 mb-4">Common Use Cases</h3>
        
        <div className="space-y-4">
          <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700">
            <h4 className="font-bold text-slate-300 mb-2">🎯 A/B Testing</h4>
            <p className="text-sm text-slate-400">Compare different traffic patterns to find the optimal configuration</p>
          </div>

          <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700">
            <h4 className="font-bold text-slate-300 mb-2">🔧 Optimization</h4>
            <p className="text-sm text-slate-400">Test different parameters and compare results to optimize performance</p>
          </div>

          <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700">
            <h4 className="font-bold text-slate-300 mb-2">📈 Benchmarking</h4>
            <p className="text-sm text-slate-400">Compare simulations to establish performance baselines</p>
          </div>

          <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700">
            <h4 className="font-bold text-slate-300 mb-2">🧪 Research</h4>
            <p className="text-sm text-slate-400">Analyze effects of different slice configurations and patterns</p>
          </div>
        </div>
      </div>

      {/* Tips */}
      <div className="card bg-slate-900/60 border-purple-500/30">
        <h3 className="text-xl font-bold text-purple-400 mb-4">💡 Pro Tips</h3>
        <ul className="space-y-3 text-slate-300">
          <li className="flex gap-3">
            <span className="text-purple-400">•</span>
            <span>For meaningful comparisons, use simulations with different patterns but similar durations</span>
          </li>
          <li className="flex gap-3">
            <span className="text-purple-400">•</span>
            <span>Pay attention to the highlighted winner in each metric category</span>
          </li>
          <li className="flex gap-3">
            <span className="text-purple-400">•</span>
            <span>Look at success rates to determine overall performance</span>
          </li>
          <li className="flex gap-3">
            <span className="text-purple-400">•</span>
            <span>Use comparison results to inform your network configuration decisions</span>
          </li>
        </ul>
      </div>
    </div>
  );
}