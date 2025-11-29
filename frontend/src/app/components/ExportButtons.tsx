'use client';

import React, { useState } from 'react';
import { Download, FileJson, FileText } from 'lucide-react';

interface ExportButtonsProps {
  simulationId: string | null;
  metricsHistory: any[];
  isEnabled?: boolean;
}

export default function ExportButtons({ 
  simulationId, 
  metricsHistory, 
  isEnabled = true 
}: ExportButtonsProps) {
  const [exporting, setExporting] = useState<'csv' | 'json' | null>(null);

  const handleExport = async (format: 'csv' | 'json') => {
    if (!simulationId) {
      alert('No simulation to export');
      return;
    }

    setExporting(format);

    try {
      if (format === 'csv') {
        exportCSV();
      } else {
        exportJSON();
      }
    } catch (error) {
      console.error('Error exporting:', error);
      alert('Export failed');
    } finally {
      setExporting(null);
    }
  };

  const exportCSV = () => {
    if (metricsHistory.length === 0) {
      alert('No data to export');
      return;
    }

    const headers = [
      'Timestamp',
      'Traffic Generated',
      'Packets Processed',
      'Packets Dropped',
      'Success Rate (%)',
      'eMBB Latency (ms)',
      'URLLC Latency (ms)',
      'mMTC Latency (ms)',
      'eMBB Throughput (Mbps)',
      'URLLC Reliability (%)',
      'mMTC Devices',
    ];

    const rows = metricsHistory.map((metric) => {
      const successRate = metric.total_traffic_generated > 0
        ? ((metric.total_packets_processed - metric.total_packets_dropped) / 
           metric.total_traffic_generated) * 100
        : 0;

      return [
        metric.timestamp,
        metric.total_traffic_generated,
        metric.total_packets_processed,
        metric.total_packets_dropped,
        successRate.toFixed(2),
        metric.slice_metrics?.embb?.metrics?.latency?.avg || 0,
        metric.slice_metrics?.urllc?.metrics?.latency?.avg || 0,
        metric.slice_metrics?.mmtc?.metrics?.latency?.avg || 0,
        metric.slice_metrics?.embb?.metrics?.throughput?.avg || 0,
        metric.slice_metrics?.urllc?.reliability_index || 0,
        metric.slice_metrics?.mmtc?.active_devices || 0,
      ];
    });

    const csv = [
      headers.join(','),
      ...rows.map((row) => row.join(',')),
    ].join('\n');

    downloadFile(csv, `${simulationId}_export.csv`, 'text/csv');
  };

  const exportJSON = () => {
    if (metricsHistory.length === 0) {
      alert('No data to export');
      return;
    }

    const data = {
      simulation_id: simulationId,
      export_date: new Date().toISOString(),
      metrics_count: metricsHistory.length,
      metrics: metricsHistory.map((metric) => ({
        timestamp: metric.timestamp,
        traffic_generated: metric.total_traffic_generated,
        packets_processed: metric.total_packets_processed,
        packets_dropped: metric.total_packets_dropped,
        success_rate:
          metric.total_traffic_generated > 0
            ? ((metric.total_packets_processed - metric.total_packets_dropped) /
               metric.total_traffic_generated) *
              100
            : 0,
        slice_metrics: {
          embb: {
            latency_avg: metric.slice_metrics?.embb?.metrics?.latency?.avg,
            throughput_avg: metric.slice_metrics?.embb?.metrics?.throughput?.avg,
            qos_compliance: metric.slice_metrics?.embb?.qos_compliance_rate,
          },
          urllc: {
            latency_avg: metric.slice_metrics?.urllc?.metrics?.latency?.avg,
            reliability: metric.slice_metrics?.urllc?.reliability_index,
            retransmitted: metric.slice_metrics?.urllc?.packets_retransmitted,
          },
          mmtc: {
            latency_avg: metric.slice_metrics?.mmtc?.metrics?.latency?.avg,
            active_devices: metric.slice_metrics?.mmtc?.active_devices,
            success_rate: metric.slice_metrics?.mmtc?.success_rate,
          },
        },
      })),
    };

    downloadFile(
      JSON.stringify(data, null, 2),
      `${simulationId}_export.json`,
      'application/json'
    );
  };

  const downloadFile = (content: string, filename: string, type: string) => {
    const blob = new Blob([content], { type });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="flex gap-4 flex-wrap">
      <button
        onClick={() => handleExport('csv')}
        disabled={!isEnabled || exporting === 'csv'}
        className="btn-primary flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        title="Export as CSV"
      >
        {exporting === 'csv' ? (
          <>
            <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full"></div>
            Exporting CSV...
          </>
        ) : (
          <>
            <FileText size={20} />
            Export CSV
          </>
        )}
      </button>

      <button
        onClick={() => handleExport('json')}
        disabled={!isEnabled || exporting === 'json'}
        className="btn-primary flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        title="Export as JSON"
      >
        {exporting === 'json' ? (
          <>
            <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full"></div>
            Exporting JSON...
          </>
        ) : (
          <>
            <FileJson size={20} />
            Export JSON
          </>
        )}
      </button>

      {!isEnabled && (
        <div className="flex items-center gap-2 px-4 py-3 bg-slate-800/50 rounded-lg border border-slate-700">
          <Download size={20} className="text-slate-500" />
          <span className="text-sm text-slate-400">Start a simulation to enable exports</span>
        </div>
      )}
    </div>
  );
}