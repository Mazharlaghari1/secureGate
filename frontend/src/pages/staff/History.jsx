import React, { useEffect, useState } from 'react';
import api from '../../services/api';
import {
  History,
  Clock,
  User,
  Ticket,
  MapPin,
  CheckCircle,
  XCircle,
  RefreshCw,
  Search,
  Filter
} from 'lucide-react';

export default function HistoryPage() {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/api/attendance/my-scans?page=${page}&page_size=${pageSize}`);
      setScans(res.data.data);
      setTotal(res.data.total);
    } catch (err) {
      console.error('Failed to load check-in scans history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [page]);

  const totalPages = Math.ceil(total / pageSize);

  // Compute status metrics for the current page
  const successCount = scans.filter(s => s.status === 'success' || s.status === 'checked_in').length;
  const failCount = scans.length - successCount;

  return (
    <div className="p-6 md:p-8 max-w-4xl mx-auto space-y-6">
      
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight flex items-center space-x-2.5">
            <span>Your Scan History</span>
          </h1>
          <p className="text-slate-500 text-sm mt-0.5 font-medium">
            Monitor and audit check-ins authorized under your scanner profile.
          </p>
        </div>
        <button
          onClick={fetchHistory}
          className="flex items-center space-x-2 px-3.5 py-2 bg-white hover:bg-slate-50 text-slate-700 hover:text-slate-900 border border-slate-200 rounded-lg text-xs font-bold transition-all shadow-xs cursor-pointer"
        >
          <RefreshCw className="h-3.5 w-3.5 text-slate-450" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Stats Summary cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-150 shadow-xs">
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Total Scans (All time)</span>
          <p className="text-xl font-extrabold text-slate-850 mt-0.5">{total}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-150 shadow-xs">
          <span className="text-[10px] text-slate-450 font-bold uppercase tracking-wider block">Page Successes</span>
          <p className="text-xl font-extrabold text-emerald-650 mt-0.5">{successCount}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-150 shadow-xs">
          <span className="text-[10px] text-slate-450 font-bold uppercase tracking-wider block">Page Denials</span>
          <p className="text-xl font-extrabold text-red-650 mt-0.5">{failCount}</p>
        </div>
      </div>

      {/* History table */}
      {loading ? (
        <div className="bg-white rounded-xl border border-slate-150 overflow-hidden shadow-xs divide-y divide-slate-100 animate-pulse">
          {[1, 2, 3].map(i => (
            <div key={i} className="p-5 flex justify-between items-center">
              <div className="space-y-1.5 w-1/4">
                <div className="h-3.5 bg-slate-200 rounded"></div>
                <div className="h-3 bg-slate-200 rounded w-2/3"></div>
              </div>
              <div className="h-4 bg-slate-200 rounded w-24"></div>
              <div className="h-4 bg-slate-200 rounded w-16"></div>
              <div className="h-4 bg-slate-200 rounded w-28"></div>
            </div>
          ))}
        </div>
      ) : scans.length === 0 ? (
        <div className="text-center py-16 bg-white border border-slate-150 rounded-xl shadow-xs flex flex-col items-center justify-center p-6">
          <div className="p-3 bg-slate-50 rounded-full text-slate-400 mb-3.5">
            <History className="h-8 w-8" />
          </div>
          <h3 className="text-sm font-bold text-slate-900 tracking-tight">No Scans Recorded</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm">
            Launch the gate scanner to start checking in participants and validating event codes.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-slate-150 shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm text-slate-555">
                <thead className="bg-slate-50 text-[10px] text-slate-450 font-bold uppercase tracking-wider border-b border-slate-150">
                  <tr>
                    <th className="px-6 py-4">Attendee Name</th>
                    <th className="px-6 py-4">Ticket Code</th>
                    <th className="px-6 py-4">Event Name</th>
                    <th className="px-6 py-4">Checked In At</th>
                    <th className="px-6 py-4">Result</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium text-slate-800">
                  {scans.map((scan, idx) => {
                    const isSuccess = scan.status === 'success' || scan.status === 'checked_in';
                    return (
                      <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-6 py-4 font-semibold text-slate-900">{scan.participant_name}</td>
                        <td className="px-6 py-4">
                          <span className="font-mono text-xs bg-slate-100 text-slate-800 px-2 py-0.5 rounded border border-slate-200 font-bold tracking-wider">
                            {scan.ticket_code}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-xs">{scan.event_name}</td>
                        <td className="px-6 py-4 text-xs font-mono text-slate-500">
                          {new Date(scan.scanned_at).toLocaleString()}
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center space-x-1 text-[10px] font-bold uppercase px-2 py-0.5 border rounded-full ${
                            isSuccess 
                              ? 'bg-green-50 text-green-700 border-green-200' 
                              : 'bg-red-50 text-red-700 border-red-200'
                          }`}>
                            {isSuccess ? 'Granted' : 'Denied'}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between text-xs font-semibold text-slate-550 pt-2 bg-white p-4 rounded-xl border border-slate-150 shadow-xs">
              <span>
                Page {page} of {totalPages} (Total scans: {total})
              </span>
              <div className="flex space-x-2">
                <button
                  onClick={() => setPage(p => Math.max(p - 1, 1))}
                  disabled={page === 1}
                  className="px-3 py-1.5 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-700 font-bold transition-colors disabled:opacity-50 cursor-pointer"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage(p => Math.min(p + 1, totalPages))}
                  disabled={page === totalPages}
                  className="px-3 py-1.5 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-700 font-bold transition-colors disabled:opacity-50 cursor-pointer"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
