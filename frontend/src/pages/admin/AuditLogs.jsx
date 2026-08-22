import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import {
  ShieldAlert,
  Search,
  Filter,
  CheckCircle,
  XCircle,
  Clock,
  User,
  Activity,
  ArrowRight,
  RefreshCw,
  SlidersHorizontal,
  ChevronDown,
  ChevronRight
} from 'lucide-react';

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [actionFilter, setActionFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [expandedLogId, setExpandedLogId] = useState(null);
  const pageSize = 20;

  const fetchLogs = async () => {
    setLoading(true);
    try {
      let url = `/api/audit-logs?page=${page}&page_size=${pageSize}`;
      if (actionFilter) url += `&action=${actionFilter}`;
      if (statusFilter) url += `&status=${statusFilter}`;
      
      const res = await api.get(url);
      setLogs(res.data.data);
      setTotal(res.data.total);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [page, actionFilter, statusFilter]);

  const totalPages = Math.ceil(total / pageSize);

  const getActionStyle = (action) => {
    if (action.includes('REVOKED') || action.includes('DEACTIVATED') || action.includes('FAILURE') || action.includes('REJECTED')) {
      return 'bg-red-50 text-red-750 border-red-150';
    }
    if (action.includes('CREATED') || action.includes('IMPORT_SUCCESS') || action.includes('GENERATED') || action.includes('CHECKED_IN') || action.includes('LOGIN')) {
      return 'bg-emerald-50 text-emerald-750 border-emerald-150';
    }
    return 'bg-indigo-50 text-indigo-750 border-indigo-150';
  };

  const getStatusIcon = (status) => {
    return status === 'success'
      ? <CheckCircle className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
      : <XCircle className="h-3.5 w-3.5 text-red-500 shrink-0" />;
  };

  const toggleRow = (logId) => {
    setExpandedLogId(expandedLogId === logId ? null : logId);
  };

  return (
    <div className="p-6 md:p-8 max-w-6xl mx-auto space-y-6">
      
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight flex items-center space-x-2.5">
            <span>Security Audit Log</span>
          </h1>
          <p className="text-slate-500 text-sm mt-0.5 font-medium">
            Monitor administrative, authentication, and access-control activity.
          </p>
        </div>
        <button
          onClick={fetchLogs}
          className="flex items-center space-x-2 px-3.5 py-2 bg-white hover:bg-slate-50 text-slate-700 hover:text-slate-900 border border-slate-200 rounded-lg text-xs font-bold transition-all shadow-xs cursor-pointer"
        >
          <RefreshCw className="h-3.5 w-3.5 text-slate-450" />
          <span>Refresh Feed</span>
        </button>
      </div>

      {/* Filters Toolbar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-white p-4 rounded-xl border border-slate-150 shadow-xs items-center">
        {/* Action filter */}
        <div className="flex items-center space-x-2 text-xs font-semibold text-slate-550">
          <SlidersHorizontal className="h-3.5 w-3.5 text-slate-400" />
          <span>Action Type:</span>
          <select
            value={actionFilter}
            onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}
            className="flex-1 sm:flex-none px-2.5 py-1.5 border border-slate-200 bg-slate-50 rounded-lg focus:outline-none text-xs font-bold text-slate-750 cursor-pointer"
          >
            <option value="">All Actions</option>
            <option value="USER_LOGIN">USER_LOGIN</option>
            <option value="EVENT_CREATED">EVENT_CREATED</option>
            <option value="EVENT_UPDATED">EVENT_UPDATED</option>
            <option value="PARTICIPANT_CREATED">PARTICIPANT_CREATED</option>
            <option value="PARTICIPANT_DEACTIVATED">PARTICIPANT_DEACTIVATED</option>
            <option value="CSV_BULK_IMPORT_SUCCESS">CSV_BULK_IMPORT_SUCCESS</option>
            <option value="CSV_BULK_IMPORT_FAILURE">CSV_BULK_IMPORT_FAILURE</option>
            <option value="TICKETS_GENERATED">TICKETS_GENERATED</option>
            <option value="TICKET_REVOKED">TICKET_REVOKED</option>
            <option value="TICKET_CHECKED_IN">TICKET_CHECKED_IN</option>
          </select>
        </div>

        {/* Status filter */}
        <div className="flex items-center space-x-2 text-xs font-semibold text-slate-550 justify-start sm:justify-end">
          <Filter className="h-3.5 w-3.5 text-slate-400" />
          <span>Status Result:</span>
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="px-2.5 py-1.5 border border-slate-200 bg-slate-50 rounded-lg focus:outline-none text-xs font-bold text-slate-755 cursor-pointer"
          >
            <option value="">All Statuses</option>
            <option value="success">Success</option>
            <option value="failure">Failure</option>
          </select>
        </div>
      </div>

      {/* Audit List Container */}
      {loading ? (
        <div className="bg-white rounded-xl border border-slate-150 overflow-hidden shadow-xs divide-y divide-slate-100 animate-pulse">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="p-5 flex justify-between items-center">
              <div className="space-y-1.5 w-1/4">
                <div className="h-3.5 bg-slate-200 rounded w-2/3"></div>
                <div className="h-3 bg-slate-200 rounded w-1/2"></div>
              </div>
              <div className="h-4.5 bg-slate-200 rounded w-28"></div>
              <div className="h-4 bg-slate-200 rounded w-12"></div>
              <div className="h-4 bg-slate-200 rounded w-1/3"></div>
            </div>
          ))}
        </div>
      ) : logs.length === 0 ? (
        <div className="text-center py-16 bg-white border border-slate-150 rounded-xl shadow-xs flex flex-col items-center justify-center p-6">
          <div className="p-3 bg-slate-50 rounded-full text-slate-400 mb-3.5">
            <ShieldAlert className="h-8 w-8" />
          </div>
          <h3 className="text-sm font-bold text-slate-900 tracking-tight">No Audit Logs Recorded</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm">
            {actionFilter || statusFilter 
              ? "No log entries match the selected filters. Clear them to inspect audit logs."
              : "Audit trail is empty. Security activities will be logged dynamically."}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-slate-150 shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm text-slate-550">
                <thead className="bg-slate-50 text-[10px] text-slate-450 font-bold uppercase tracking-wider border-b border-slate-150">
                  <tr>
                    <th className="px-6 py-4 w-10"></th>
                    <th className="px-6 py-4">Timestamp</th>
                    <th className="px-6 py-4">Actor</th>
                    <th className="px-6 py-4">Action</th>
                    <th className="px-6 py-4">Target Resource</th>
                    <th className="px-6 py-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium text-slate-800">
                  {logs.map((log) => {
                    const isExpanded = expandedLogId === log.id;
                    return (
                      <React.Fragment key={log.id}>
                        <tr 
                          onClick={() => toggleRow(log.id)}
                          className="hover:bg-slate-50/50 transition-colors cursor-pointer"
                        >
                          <td className="px-6 py-4 text-center">
                            {isExpanded ? (
                              <ChevronDown className="h-4 w-4 text-slate-400" />
                            ) : (
                              <ChevronRight className="h-4 w-4 text-slate-400" />
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-xs font-mono text-slate-500 flex items-center space-x-2">
                            <Clock className="h-3.5 w-3.5 text-slate-400" />
                            <span>{new Date(log.timestamp).toLocaleString()}</span>
                          </td>
                          <td className="px-6 py-4 text-slate-900 font-semibold">{log.actor_email || 'System'}</td>
                          <td className="px-6 py-4">
                            <span className={`inline-block font-mono text-[10px] px-2 py-0.5 border rounded-md font-bold tracking-tight ${getActionStyle(log.action)}`}>
                              {log.action}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-xs font-mono text-slate-450">
                            {log.target_type} ({log.target_id || 'N/A'})
                          </td>
                          <td className="px-6 py-4">
                            <span className="flex items-center space-x-1.5 text-xs font-bold capitalize">
                              {getStatusIcon(log.status)}
                              <span className={log.status === 'success' ? 'text-emerald-700' : 'text-red-750'}>
                                {log.status}
                              </span>
                            </span>
                          </td>
                        </tr>

                        {/* Collapsible Details Panel */}
                        {isExpanded && (
                          <tr className="bg-slate-50/30">
                            <td colSpan={6} className="px-12 py-4 border-t border-slate-100">
                              <div className="space-y-2">
                                <h4 className="text-xs font-bold text-slate-450 uppercase tracking-wider flex items-center space-x-1">
                                  <Activity className="h-3.5 w-3.5" />
                                  <span>Log Metadata Details</span>
                                </h4>
                                
                                {Object.keys(log.metadata).length === 0 ? (
                                  <span className="text-xs text-slate-450 italic">No additional metadata logged.</span>
                                ) : (
                                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 bg-slate-50 p-4 rounded-lg border border-slate-150 font-mono text-xs">
                                    {Object.entries(log.metadata).map(([k, v]) => (
                                      <div key={k} className="flex space-x-2">
                                        <span className="text-slate-450 font-bold shrink-0">{k}:</span>
                                        <span className="text-slate-700 break-all">{typeof v === 'object' ? JSON.stringify(v) : String(v)}</span>
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
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
                Page {page} of {totalPages} (Total audits: {total})
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
