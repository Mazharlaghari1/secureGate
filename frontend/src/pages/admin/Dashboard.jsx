import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import {
  Calendar,
  Users,
  Ticket,
  CheckCircle2,
  RefreshCw,
  Plus,
  ArrowUpRight,
  TrendingUp,
  HelpCircle,
  Building,
  Hourglass,
  Clock
} from 'lucide-react';

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [events, setEvents] = useState([]);
  const [selectedEventId, setSelectedEventId] = useState('');
  const [eventStats, setEventStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [eventLoading, setEventLoading] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const fetchGlobalStats = async () => {
    try {
      const res = await api.get('/api/reports/dashboard');
      setStats(res.data.data);
    } catch (err) {
      console.error('Failed to load global dashboard stats:', err);
    }
  };

  const fetchEvents = async () => {
    try {
      const res = await api.get('/api/events?page_size=100');
      setEvents(res.data.data);
      if (res.data.data.length > 0 && !selectedEventId) {
        setSelectedEventId(res.data.data[0].id);
      }
    } catch (err) {
      console.error('Failed to load events:', err);
    }
  };

  const fetchEventStats = async (eventId) => {
    if (!eventId) return;
    setEventLoading(true);
    try {
      const res = await api.get(`/api/reports/event/${eventId}`);
      setEventStats(res.data.data);
    } catch (err) {
      console.error('Failed to load event-specific stats:', err);
    } finally {
      setEventLoading(false);
    }
  };

  const initDashboard = async () => {
    setLoading(true);
    await Promise.all([fetchGlobalStats(), fetchEvents()]);
    setLoading(false);
    showToast('Dashboard stats refreshed.');
  };

  useEffect(() => {
    initDashboard();
  }, []);

  useEffect(() => {
    if (selectedEventId) {
      fetchEventStats(selectedEventId);
    }
  }, [selectedEventId]);

  if (loading) {
    return (
      <div className="p-8 max-w-6xl mx-auto space-y-6 animate-pulse">
        <div className="h-8 bg-slate-200 rounded w-1/4"></div>
        <div className="h-12 bg-slate-200 rounded w-1/2"></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-32 bg-slate-200 rounded-xl"></div>
          ))}
        </div>
        <div className="h-96 bg-slate-200 rounded-xl"></div>
      </div>
    );
  }

  // Get active event details from dropdown selection
  const activeEvent = events.find(e => e.id === selectedEventId);

  return (
    <div className="relative p-6 md:p-8 max-w-6xl mx-auto space-y-8">
      {/* Toast Alert */}
      {toastMessage && (
        <div className="fixed bottom-4 right-4 bg-slate-900 border border-slate-800 text-slate-100 px-4 py-3 rounded-lg shadow-xl text-xs flex items-center space-x-2 animate-bounce z-50">
          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Top Header Row */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-450 uppercase tracking-wider">
            <span>Administration</span>
            <span className="text-slate-300">/</span>
            <span>Dashboard</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-900 mt-1.5 tracking-tight">
            Good morning, {user?.name || 'Administrator'}
          </h1>
          <p className="text-slate-500 text-sm mt-0.5 font-medium">
            Monitor events, registrations, tickets, and access activity.
          </p>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          <button
            onClick={initDashboard}
            className="flex items-center space-x-2 px-3 py-2 bg-white hover:bg-slate-50 text-slate-700 hover:text-slate-900 border border-slate-200 rounded-lg text-sm font-semibold transition-all shadow-xs cursor-pointer"
          >
            <RefreshCw className="h-4 w-4 text-slate-450" />
            <span>Refresh</span>
          </button>
          <button
            onClick={() => navigate('/admin/events')}
            className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-750 text-white rounded-lg text-sm font-semibold transition-all shadow-sm shadow-indigo-600/10 cursor-pointer"
          >
            <Plus className="h-4 w-4" />
            <span>Create Event</span>
          </button>
        </div>
      </div>

      {/* Global Stat Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
          {/* Card 1: Total Events */}
          <div className="bg-white p-5 rounded-xl border border-slate-150 shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow relative overflow-hidden group">
            <div className="flex justify-between items-start">
              <span className="text-xs font-bold text-slate-450 uppercase tracking-wider">Total Events</span>
              <div className="p-2 bg-slate-50 text-slate-500 rounded-lg group-hover:bg-indigo-50 group-hover:text-indigo-650 transition-colors">
                <Calendar className="h-4.5 w-4.5" />
              </div>
            </div>
            <div className="mt-4">
              <span className="text-3xl font-extrabold text-slate-900 tracking-tight">{stats.total_events}</span>
              <div className="flex items-center space-x-1 mt-1 text-slate-450 text-xs font-medium">
                <TrendingUp className="h-3.5 w-3.5 text-emerald-500" />
                <span>All time published</span>
              </div>
            </div>
          </div>

          {/* Card 2: Active Events */}
          <div className="bg-white p-5 rounded-xl border border-slate-150 shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow relative overflow-hidden group">
            <div className="flex justify-between items-start">
              <span className="text-xs font-bold text-slate-450 uppercase tracking-wider">Active Events</span>
              <div className="p-2 bg-emerald-50/50 text-emerald-600 rounded-lg group-hover:bg-emerald-50 group-hover:text-emerald-700 transition-colors">
                <CheckCircle2 className="h-4.5 w-4.5" />
              </div>
            </div>
            <div className="mt-4">
              <span className="text-3xl font-extrabold text-slate-900 tracking-tight">{stats.active_events}</span>
              <div className="flex items-center space-x-1 mt-1 text-slate-450 text-xs font-medium">
                <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></div>
                <span className="text-emerald-600 font-semibold">Live and scanning</span>
              </div>
            </div>
          </div>

          {/* Card 3: Total Registrations */}
          <div className="bg-white p-5 rounded-xl border border-slate-150 shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow relative overflow-hidden group">
            <div className="flex justify-between items-start">
              <span className="text-xs font-bold text-slate-450 uppercase tracking-wider">Total Participants</span>
              <div className="p-2 bg-slate-50 text-slate-500 rounded-lg group-hover:bg-indigo-50 group-hover:text-indigo-650 transition-colors">
                <Users className="h-4.5 w-4.5" />
              </div>
            </div>
            <div className="mt-4">
              <span className="text-3xl font-extrabold text-slate-900 tracking-tight">{stats.total_registered_participants}</span>
              <div className="flex items-center space-x-1 mt-1 text-slate-450 text-xs font-medium">
                <ArrowUpRight className="h-3.5 w-3.5 text-indigo-500" />
                <span>Across all segments</span>
              </div>
            </div>
          </div>

          {/* Card 4: Tickets Allocated */}
          <div className="bg-white p-5 rounded-xl border border-slate-150 shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow relative overflow-hidden group">
            <div className="flex justify-between items-start">
              <span className="text-xs font-bold text-slate-450 uppercase tracking-wider">Tickets Issued</span>
              <div className="p-2 bg-slate-50 text-slate-500 rounded-lg group-hover:bg-indigo-50 group-hover:text-indigo-650 transition-colors">
                <Ticket className="h-4.5 w-4.5" />
              </div>
            </div>
            <div className="mt-4">
              <span className="text-3xl font-extrabold text-slate-900 tracking-tight">{stats.total_allocated_tickets}</span>
              <div className="flex items-center space-x-1 mt-1 text-slate-450 text-xs font-medium">
                <span>Active barcodes generated</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Analytics Container: Grid split into details & chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column (2/3 width on large screens): Timeline Chart */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-150 shadow-xs p-6 flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-start mb-6">
              <div>
                <h3 className="text-base font-bold text-slate-900 tracking-tight">Check-in Activity</h3>
                <p className="text-xs text-slate-450 mt-0.5 font-medium">Scans recorded per hour for the selected event.</p>
              </div>

              {/* Event Selector in Chart Header */}
              <div className="w-52 shrink-0">
                <select
                  value={selectedEventId}
                  onChange={(e) => setSelectedEventId(e.target.value)}
                  className="w-full px-3 py-1.5 border border-slate-200 hover:border-slate-350 bg-slate-50 rounded-lg focus:ring-1 focus:ring-indigo-500 focus:outline-none text-xs font-semibold text-slate-700 cursor-pointer"
                >
                  {events.length === 0 ? (
                    <option value="">No Events Found</option>
                  ) : (
                    events.map((e) => (
                      <option key={e.id} value={e.id}>
                        {e.name}
                      </option>
                    ))
                  )}
                </select>
              </div>
            </div>

            {eventLoading ? (
              <div className="flex flex-col items-center justify-center h-64 text-slate-450 text-sm space-y-2">
                <RefreshCw className="h-6 w-6 animate-spin text-indigo-500" />
                <span>Fetching event analytics...</span>
              </div>
            ) : eventStats && eventStats.check_ins_over_time.length > 0 ? (
              <div className="relative pt-6">
                {/* Horizontal Guide Lines */}
                <div className="absolute inset-0 flex flex-col justify-between pointer-events-none pb-8 pt-6">
                  {[1, 2, 3].map((_, index) => (
                    <div key={index} className="w-full border-t border-slate-100 border-dashed"></div>
                  ))}
                </div>

                <div className="relative flex h-60 items-end space-x-4 md:space-x-6 px-4">
                  {eventStats.check_ins_over_time.map((bin, idx) => {
                    const maxCount = Math.max(...eventStats.check_ins_over_time.map(b => b.count), 1);
                    const heightPercent = (bin.count / maxCount) * 100;
                    return (
                      <div key={idx} className="flex-1 flex flex-col items-center h-full justify-end group z-10">
                        {/* Count Tooltip */}
                        <div className="absolute opacity-0 group-hover:opacity-100 bg-slate-900 text-white text-[10px] font-bold px-2 py-1 rounded shadow-md -translate-y-16 transition-opacity pointer-events-none whitespace-nowrap">
                          {bin.count} scans
                        </div>
                        <div className="text-[11px] font-bold text-slate-800 mb-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          {bin.count}
                        </div>
                        <div
                          style={{ height: `${heightPercent}%` }}
                          className="w-full bg-indigo-600 hover:bg-indigo-750 rounded-t-md transition-all duration-300 shadow-sm"
                        ></div>
                        <div className="text-[10px] text-slate-450 mt-2.5 font-mono tracking-tight font-semibold whitespace-nowrap">
                          {bin.hour}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-64 border border-dashed border-slate-200 rounded-xl bg-slate-50/50 p-6 text-center">
                <Clock className="h-8 w-8 text-slate-400 mb-2" />
                <p className="text-sm font-semibold text-slate-800">No Check-in Activity Yet</p>
                <p className="text-xs text-slate-500 mt-1 max-w-sm">No ticket check-in timestamps have been logged for this event. Launch the staff scanner to begin scanning barcodes.</p>
              </div>
            )}
          </div>
        </div>

        {/* Right Column (1/3 width): Selected Event Details */}
        <div className="bg-white rounded-xl border border-slate-150 shadow-xs p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900 tracking-tight mb-5">Event Specific Insights</h3>
            
            {activeEvent && (
              <div className="space-y-4 mb-6">
                <div>
                  <h4 className="text-sm font-bold text-slate-850 truncate">{activeEvent.name}</h4>
                  <span className={`inline-block text-[10px] px-2 py-0.5 border rounded-full font-bold uppercase mt-1.5 ${
                    activeEvent.status === 'active' ? 'bg-green-50 text-green-700 border-green-200' :
                    activeEvent.status === 'completed' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                    activeEvent.status === 'cancelled' ? 'bg-red-50 text-red-700 border-red-200' :
                    'bg-slate-50 text-slate-550 border-slate-200'
                  }`}>
                    {activeEvent.status}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4 text-xs font-semibold text-slate-550 border-t border-slate-100 pt-4">
                  <div className="flex items-center space-x-1.5">
                    <Building className="h-4 w-4 text-slate-400" />
                    <span className="truncate">{activeEvent.venue}</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <Calendar className="h-4 w-4 text-slate-400" />
                    <span>{activeEvent.date}</span>
                  </div>
                </div>
              </div>
            )}

            {eventLoading ? (
              <div className="space-y-4 py-4 animate-pulse">
                <div className="h-4 bg-slate-100 rounded w-3/4"></div>
                <div className="h-4 bg-slate-100 rounded w-5/6"></div>
                <div className="h-4 bg-slate-100 rounded w-2/3"></div>
              </div>
            ) : eventStats ? (
              <div className="space-y-5 border-t border-slate-100 pt-5">
                {/* Tickets Issued Progress */}
                <div>
                  <div className="flex justify-between items-center text-xs font-semibold text-slate-550 mb-1.5">
                    <span>Registered / Capacity</span>
                    <span className="text-slate-850 font-bold">
                      {eventStats.tickets_issued} / {activeEvent?.capacity || 0}
                    </span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div 
                      style={{ width: `${Math.min((eventStats.tickets_issued / (activeEvent?.capacity || 1)) * 100, 100)}%` }}
                      className="h-full bg-indigo-600 rounded-full transition-all duration-500"
                    ></div>
                  </div>
                </div>

                {/* Check-ins Progress */}
                <div>
                  <div className="flex justify-between items-center text-xs font-semibold text-slate-550 mb-1.5">
                    <span>Checked In / Registered</span>
                    <span className="text-slate-850 font-bold">
                      {eventStats.checked_in} / {eventStats.tickets_issued}
                    </span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div 
                      style={{ width: `${Math.min((eventStats.checked_in / (eventStats.tickets_issued || 1)) * 100, 100)}%` }}
                      className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                    ></div>
                  </div>
                </div>

                {/* Additional detailed items */}
                <div className="grid grid-cols-2 gap-4 border-t border-slate-100 pt-4">
                  <div className="bg-slate-50/50 p-3 rounded-lg border border-slate-150">
                    <span className="text-[10px] text-slate-450 font-bold uppercase tracking-wider">Remaining</span>
                    <p className="text-lg font-extrabold text-slate-850 mt-0.5">{eventStats.remaining}</p>
                  </div>
                  <div className="bg-slate-50/50 p-3 rounded-lg border border-slate-150">
                    <span className="text-[10px] text-slate-450 font-bold uppercase tracking-wider">Attendance %</span>
                    <p className="text-lg font-extrabold text-indigo-650 mt-0.5">{eventStats.attendance_percentage}%</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-slate-400 text-xs">No insights loaded.</div>
            )}
          </div>

          {selectedEventId && (
            <button
              onClick={() => navigate(`/admin/events/${selectedEventId}`)}
              className="mt-6 w-full py-2 bg-slate-900 hover:bg-slate-950 text-white rounded-lg text-xs font-bold transition-all shadow-xs cursor-pointer"
            >
              Manage Registration &rarr;
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
