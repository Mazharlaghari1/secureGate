import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import {
  Calendar,
  Search,
  Filter,
  MapPin,
  Clock,
  ChevronRight,
  RefreshCw,
  SlidersHorizontal
} from 'lucide-react';

export default function PortalEvents() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [timeFilter, setTimeFilter] = useState('all'); // 'all' | 'upcoming' | 'past'

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/portal/events');
      setEvents(res.data.data);
    } catch (err) {
      console.error('Failed to load registered events:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  const todayStr = new Date().toISOString().split('T')[0];

  const filteredEvents = events.filter(e => {
    const matchesSearch = e.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          e.venue.toLowerCase().includes(searchQuery.toLowerCase());
    
    if (timeFilter === 'upcoming') {
      return matchesSearch && e.date >= todayStr;
    }
    if (timeFilter === 'past') {
      return matchesSearch && e.date < todayStr;
    }
    return matchesSearch;
  });

  return (
    <div className="p-6 md:p-8 max-w-6xl mx-auto space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">My Registered Events</h1>
          <p className="text-slate-500 text-sm mt-0.5 font-medium">
            Browse and inspect events you are enrolled in.
          </p>
        </div>
        <button
          onClick={fetchEvents}
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
            placeholder="Search events by name or venue..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-slate-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-lg text-sm focus:outline-none transition-all placeholder-slate-400 bg-slate-50/50"
          />
        </div>

        {/* Time filters */}
        <div className="flex items-center space-x-2 text-xs font-semibold text-slate-555 w-full sm:w-auto">
          <SlidersHorizontal className="h-3.5 w-3.5 text-slate-400" />
          <span>Timing Filter:</span>
          <select
            value={timeFilter}
            onChange={(e) => setTimeFilter(e.target.value)}
            className="px-2.5 py-1.5 border border-slate-200 bg-slate-50 rounded-lg focus:outline-none text-xs font-bold text-slate-700 cursor-pointer"
          >
            <option value="all">All Events</option>
            <option value="upcoming">Upcoming Events</option>
            <option value="past">Past Events</option>
          </select>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-pulse">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-44 bg-slate-200 rounded-xl"></div>
          ))}
        </div>
      ) : filteredEvents.length === 0 ? (
        <div className="text-center py-16 bg-white border border-slate-150 rounded-xl shadow-xs flex flex-col items-center justify-center p-6">
          <div className="p-3 bg-slate-50 rounded-full text-slate-400 mb-3.5">
            <Calendar className="h-8 w-8" />
          </div>
          <h3 className="text-sm font-bold text-slate-900 tracking-tight">No Events Found</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm">
            No registered events match your search term or timing filter.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredEvents.map(e => (
            <div key={e.id} className="bg-white rounded-xl border border-slate-150 shadow-xs p-5 flex flex-col justify-between hover:shadow-md transition-all">
              <div className="space-y-4">
                <div className="flex justify-between items-start">
                  <h4 className="text-base font-bold text-slate-850 line-clamp-1 leading-snug">{e.name}</h4>
                  <span className={`inline-block text-[9px] px-2 py-0.5 border rounded-full font-bold uppercase ${
                    e.checked_in 
                      ? 'bg-green-50 text-green-700 border-green-200' 
                      : 'bg-slate-50 text-slate-600 border-slate-200'
                  }`}>
                    {e.checked_in ? '✓ Checked in' : 'Not checked in'}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3.5 text-xs font-semibold text-slate-500">
                  <div className="flex items-center space-x-1.5">
                    <Calendar className="h-4 w-4 text-slate-400 shrink-0" />
                    <span>{e.date}</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <Clock className="h-4 w-4 text-slate-400 shrink-0" />
                    <span>{e.start_time} - {e.end_time}</span>
                  </div>
                  <div className="flex items-center space-x-1.5 col-span-2">
                    <MapPin className="h-4 w-4 text-slate-400 shrink-0" />
                    <span className="truncate">{e.venue}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between border-t border-slate-100 mt-5 pt-4">
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                  Ticket:{' '}
                  {e.ticket_status ? (
                    <span className="text-indigo-650 font-mono font-extrabold select-all tracking-wider ml-1">
                      {e.ticket_code} ({e.ticket_status})
                    </span>
                  ) : (
                    <span className="text-slate-400 italic font-semibold ml-1">Unassigned</span>
                  )}
                </div>

                <Link
                  to={`/portal/events/${e.id}`}
                  className="inline-flex items-center space-x-1 px-3 py-1.5 bg-slate-50 hover:bg-indigo-50 border border-slate-200 hover:border-indigo-200 rounded-lg text-xs font-bold text-slate-700 hover:text-indigo-650 transition-all cursor-pointer"
                >
                  <span>Manage</span>
                  <ChevronRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
