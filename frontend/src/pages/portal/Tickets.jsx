import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import {
  Ticket,
  Search,
  Filter,
  Calendar,
  MapPin,
  Clock,
  ChevronRight,
  RefreshCw,
  SlidersHorizontal
} from 'lucide-react';

export default function PortalTickets() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all'); // 'all' | 'active' | 'used' | 'revoked' | 'expired'

  const fetchTickets = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/portal/tickets');
      setTickets(res.data.data);
    } catch (err) {
      console.error('Failed to load portal tickets:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, []);

  const filteredTickets = tickets.filter(t => {
    const matchesSearch = t.event_name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          t.ticket_code.toLowerCase().includes(searchQuery.toLowerCase());
    
    if (statusFilter === 'all') return matchesSearch;
    return matchesSearch && t.status === statusFilter;
  });

  return (
    <div className="p-6 md:p-8 max-w-6xl mx-auto space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">My Access Passes</h1>
          <p className="text-slate-500 text-sm mt-0.5 font-medium">
            Manage and view your active gate-entry passes.
          </p>
        </div>
        <button
          onClick={fetchTickets}
          className="flex items-center space-x-2 px-3.5 py-2 bg-white hover:bg-slate-50 text-slate-700 hover:text-slate-900 border border-slate-200 rounded-lg text-xs font-bold transition-all shadow-xs cursor-pointer shrink-0"
        >
          <RefreshCw className="h-3.5 w-3.5 text-slate-450" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filters Toolbar */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between bg-white p-4 rounded-xl border border-slate-150 shadow-xs">
        {/* Search */}
        <div className="relative w-full sm:max-w-xs">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by event or ticket code..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-slate-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-lg text-sm focus:outline-none transition-all placeholder-slate-400 bg-slate-50/50"
          />
        </div>

        {/* Status filters */}
        <div className="flex items-center space-x-2 text-xs font-semibold text-slate-555 w-full sm:w-auto">
          <SlidersHorizontal className="h-3.5 w-3.5 text-slate-400" />
          <span>Ticket Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-2.5 py-1.5 border border-slate-200 bg-slate-50 rounded-lg focus:outline-none text-xs font-bold text-slate-700 cursor-pointer"
          >
            <option value="all">All Passes</option>
            <option value="active">Active</option>
            <option value="used">Used / Checked In</option>
            <option value="revoked">Revoked</option>
            <option value="expired">Expired</option>
          </select>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-pulse">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-44 bg-slate-200 rounded-xl"></div>
          ))}
        </div>
      ) : filteredTickets.length === 0 ? (
        <div className="text-center py-16 bg-white border border-slate-150 rounded-xl shadow-xs flex flex-col items-center justify-center p-6">
          <div className="p-3 bg-slate-50 rounded-full text-slate-400 mb-3.5">
            <Ticket className="h-8 w-8" />
          </div>
          <h3 className="text-sm font-bold text-slate-900 tracking-tight">No Tickets Found</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm">
            No tickets match your current filters.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {filteredTickets.map(t => (
            <div key={t.id} className="bg-white rounded-xl border border-slate-150 shadow-xs overflow-hidden flex flex-col justify-between hover:shadow-md transition-all">
              
              {/* Ticket header */}
              <div className="bg-slate-900 p-4 text-white">
                <span className={`inline-block text-[9px] px-2 py-0.5 border rounded-full font-bold uppercase tracking-wider ${
                  t.status === 'active' ? 'bg-emerald-600 border-emerald-500 text-white' :
                  t.status === 'used' ? 'bg-indigo-650 border-indigo-500 text-white' :
                  'bg-red-650 border-red-500 text-white'
                }`}>
                  {t.status === 'active' ? 'Valid Pass' : t.status}
                </span>
                <h4 className="text-sm font-bold text-slate-100 mt-2 truncate leading-tight">{t.event_name}</h4>
              </div>

              {/* Ticket details */}
              <div className="p-4 space-y-3 flex-1 flex flex-col justify-between">
                <div className="space-y-2 text-xs font-semibold text-slate-500">
                  <div className="flex items-center space-x-1.5">
                    <Calendar className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                    <span>{t.date}</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <Clock className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                    <span>{t.time}</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <MapPin className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                    <span className="truncate">{t.venue}</span>
                  </div>
                  <div className="border-t border-slate-50 pt-2 flex justify-between items-center text-[10px] font-bold text-slate-400 uppercase">
                    <span>Code:</span>
                    <span className="font-mono font-extrabold text-indigo-650 select-all tracking-wider">{t.ticket_code}</span>
                  </div>
                </div>

                <Link
                  to={`/portal/tickets/${t.id}`}
                  className="mt-4 w-full text-center py-2 bg-slate-50 hover:bg-indigo-50 border border-slate-200 hover:border-indigo-200 rounded-lg text-xs font-bold text-slate-700 hover:text-indigo-650 transition-all cursor-pointer block"
                >
                  View Ticket Pass
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
