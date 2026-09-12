import React, { useEffect, useState } from 'react';
import { useAuth } from '../store/auth';
import {
  generateReport,
  getReports,
  downloadReport,
  updateReportStatus,
  Report,
} from '../services/reports';

const VALID_YEARS = [2024, 2025, 2026];
const STATUS_STYLES: Record<string, { bg: string; text: string; border: string }> = {
  Draft: { bg: 'bg-yellow-900/40', text: 'text-yellow-300', border: 'border-yellow-700/50' },
  Generated: { bg: 'bg-blue-900/40', text: 'text-blue-300', border: 'border-blue-700/50' },
  Submitted: { bg: 'bg-green-900/40', text: 'text-green-300', border: 'border-green-700/50' },
};

export default function Reports() {
  const { isAuthenticated } = useAuth();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [statusUpdating, setStatusUpdating] = useState<string | null>(null);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [counts, setCounts] = useState({ Draft: 0, Generated: 0, Submitted: 0 });

  const fetchReports = async () => {
    setLoading(true);
    try {
      const res = await getReports();
      setReports(res.reports);
      const c = { Draft: 0, Generated: 0, Submitted: 0 };
      for (const r of res.reports) {
        if (c.hasOwnProperty(r.status)) {
          c[r.status as keyof typeof c]++;
        }
      }
      setCounts(c);
    } catch (err) {
      console.error('Failed to fetch reports:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isAuthenticated) return;
    fetchReports();
  }, [isAuthenticated]);

  const handleGenerate = async (year: number) => {
    setGenerating(true);
    try {
      await generateReport({ year });
      fetchReports();
      setShowGenerateModal(false);
    } catch (err) {
      console.error('Failed to generate report:', err);
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = async (id: string) => {
    try {
      await downloadReport(id);
    } catch (err) {
      console.error('Failed to download report:', err);
    }
  };

  const handleStatusUpdate = async (id: string, newStatus: string) => {
    setStatusUpdating(id);
    try {
      await updateReportStatus(id, { status: newStatus });
      fetchReports();
    } catch (err) {
      console.error('Failed to update report status:', err);
    } finally {
      setStatusUpdating(null);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="p-8">
        <a href="/login" className="text-green-400 underline">Login required</a>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-navy-50">IMO DCS Reports</h1>
          <p className="text-slate-400 mt-1">Manage annual compliance reports for your fleet</p>
        </div>
        <button
          onClick={() => setShowGenerateModal(true)}
          className="bg-green-600 hover:bg-green-700 text-white px-5 py-2.5 rounded-lg font-medium text-sm transition-colors shadow-lg shadow-green-900/30"
        >
          + Generate IMO DCS Report
        </button>
      </div>

      {/* Status cards */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Drafts', count: counts.Draft, color: '#EAB308', bg: 'bg-yellow-900/40', border: 'border-yellow-700/50' },
          { label: 'Generated', count: counts.Generated, color: '#3B82F6', bg: 'bg-blue-900/40', border: 'border-blue-700/50' },
          { label: 'Submitted', count: counts.Submitted, color: '#16A34A', bg: 'bg-green-900/40', border: 'border-green-700/50' },
        ].map((card) => (
          <div key={card.label} className={`${card.bg} border ${card.border} rounded-lg p-4`}>
            <div className="flex items-center gap-2 mb-2">
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: card.color }}></span>
              <p className="text-xs uppercase tracking-wider text-slate-400">{card.label}</p>
            </div>
            <p className="text-4xl font-bold" style={{ color: card.color }}>{card.count}</p>
          </div>
        ))}
      </div>

      {/* Generate modal */}
      {showGenerateModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-navy-900 border border-navy-700 rounded-xl p-6 w-[400px] max-w-[90vw]">
            <h2 className="text-xl font-bold text-navy-50 mb-4">Generate IMO DCS Report</h2>
            <p className="text-slate-400 text-sm mb-4">Select a reporting year to generate the annual compliance report.</p>
            <div className="space-y-2 mb-6">
              {VALID_YEARS.map((year) => (
                <button
                  key={year}
                  onClick={() => { handleGenerate(year); }}
                  disabled={generating}
                  className={`w-full text-left px-4 py-3 rounded-lg border transition-colors ${
                    selectedYear === year
                      ? 'border-green-500 bg-green-900/30 text-green-300'
                      : 'border-navy-700 bg-navy-800 text-navy-100 hover:border-navy-500'
                  } disabled:opacity-50`}
                >
                  <p className="font-medium text-sm">{year}</p>
                  <p className="text-xs text-slate-500">IMO DCS Annual Compliance Report</p>
                </button>
              ))}
            </div>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowGenerateModal(false)}
                className="px-4 py-2 rounded-lg text-slate-400 hover:text-white text-sm bg-navy-800 border border-navy-700 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reports table */}
      <div className="bg-navy-900 border border-navy-800 rounded-lg overflow-hidden">
        <div className="p-4 border-b border-navy-800 flex items-center justify-between">
          <h2 className="text-lg font-bold text-navy-50">All Reports</h2>
          <p className="text-xs text-slate-500">{reports.length} report(s) found</p>
        </div>
        {loading ? (
          <div className="text-slate-400 text-center py-12">Loading reports...</div>
        ) : reports.length === 0 ? (
          <div className="text-slate-500 text-center py-12">
            <p className="text-lg mb-2">No reports generated yet</p>
            <p className="text-sm">Click "Generate IMO DCS Report" to create your first report</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-navy-800">
                  {['Report ID', 'Year', 'Type', 'Created', 'Status', 'Actions'].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-xs uppercase tracking-wider text-slate-500 font-medium">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-800">
                {reports.map((report) => {
                  const ss = STATUS_STYLES[report.status] || STATUS_STYLES.Draft;
                  return (
                    <tr key={report.id} className="hover:bg-navy-800/50 transition-colors">
                      <td className="px-4 py-3">
                        <p className="text-sm font-mono text-navy-100">{report.id}</p>
                      </td>
                      <td className="px-4 py-3">
                        <p className="text-sm text-navy-300">{report.year}</p>
                      </td>
                      <td className="px-4 py-3">
                        <p className="text-sm text-slate-400">{report.report_type}</p>
                      </td>
                      <td className="px-4 py-3">
                        <p className="text-sm text-slate-400">
                          {new Date(report.generated_at).toLocaleDateString()}
                        </p>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${ss.bg} ${ss.text} ${ss.border}`}>
                          {report.status}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleDownload(report.id)}
                            className="text-green-400 hover:text-green-300 text-xs font-medium transition-colors"
                          >
                            Download PDF
                          </button>
                          {report.status === 'Generated' && (
                            <button
                              onClick={() => handleStatusUpdate(report.id, 'Submitted')}
                              disabled={statusUpdating === report.id}
                              className="text-blue-400 hover:text-blue-300 text-xs font-medium transition-colors disabled:opacity-50"
                            >
                              {statusUpdating === report.id ? '...' : 'Mark Submitted'}
                            </button>
                          )}
                          {report.status === 'Draft' && (
                            <button
                              onClick={() => handleStatusUpdate(report.id, 'Generated')}
                              disabled={statusUpdating === report.id}
                              className="text-purple-400 hover:text-purple-300 text-xs font-medium transition-colors disabled:opacity-50"
                            >
                              {statusUpdating === report.id ? '...' : 'Generate'}
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
