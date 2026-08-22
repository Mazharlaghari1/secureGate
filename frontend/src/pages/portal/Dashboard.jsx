import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import {
  Calendar,
  Ticket,
  Clock,
  MapPin,
  CheckCircle,
  TrendingUp,
  Award,
  RefreshCw,
  Search,
  ChevronRight,
  Compass
} from 'lucide-react';

export default function PortalDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [events, setEvents] = useState([]);
  const [availableEvents, setAvailableEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchPortalData = async () => {
    setLoading(true);
    try {
      const [eventsRes, availableRes] = await Promise.all([
        api.get('/api/portal/events'),
        api.get('/api/portal/events/available')
      ]);
      setEvents(eventsRes.data.data);
      setAvailableEvents(availableRes.data.data);
    } catch (err) {
      console.error('Failed to load portal events:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPortalData();
  }, []);

  if (loading) {
    return (
      <div className="p-8 max-w-6xl mx-auto space-y-6 animate-pulse">
        <div className="h-8 bg-slate-200 rounded w-1/4"></div>
        <div className="h-12 bg-slate-200 rounded w-1/2"></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-28 bg-slate-200 rounded-xl"></div>
          ))}
        </div>
        <div className="h-96 bg-slate-200 rounded-xl mt-8"></div>
      </div>
    );
  }

  const todayStr = new Date().toISOString().split('T')[0];
  const upcomingEvents = events.filter(e => e.date >= todayStr);
  const pastEvents = events.filter(e => e.date < todayStr);
  
  // Stats
  const upcomingCount = upcomingEvents.length;
  const activeTicketsCount = events.filter(e => e.ticket_status === 'active').length;
  const checkedInCount = events.filter(e => e.checked_in).length;
  const availableCount = availableEvents.length;

  return (
    <div className="p-6 md:p-8 max-w-6xl mx-auto space-y-8">
      {/* Welcome Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900 text-white p-6 rounded-2xl border border-slate-850 shadow-xl relative overflow-hidden">
        <div className="absolute inset-0 opacity-5 pointer-events-none">
          <div className="absolute inset-0" style={{
            backgroundImage: 'radial-gradient(circle, #4F46E5 1px, transparent 1px)',
            backgroundSize: '24px 24px'
          }}></div>
        </div>

        <div className="relative z-10 space-y-2">
          <div className="flex items-center space-x-1.5 text-[10px] font-bold text-indigo-400 uppercase tracking-widest">
            <span>Attendee Portal</span>
            <span className="text-slate-600">/</span>
            <span>Dashboard</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-black tracking-tight">
            Welcome back, {user?.name || 'Attendee'}
          </h1>
          <p className="text-slate-300 text-xs md:text-sm max-w-xl leading-relaxed font-medium">
            Manage registrations, view active gate passes, and discover upcoming summits.
          </p>
        </div>

        <div className="relative z-10 flex items-center space-x-3 shrink-0">
          <Link
            to="/portal/events/available"
            className="flex items-center space-x-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-755 text-white rounded-xl text-xs font-bold transition-all shadow-md shadow-indigo-650/20 cursor-pointer"
          >
            <Compass className="h-4 w-4" />
            <span>Browse Events</span>
          </Link>
          <button
            onClick={fetchPortalData}
            className="p-2.5 bg-slate-800 hover:bg-slate-750 border border-slate-700 text-slate-300 rounded-xl transition-all cursor-pointer"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Stats row (4 items) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Upcoming */}
        <div className="bg-white p-5 rounded-xl border border-slate-150 shadow-xs flex flex-col justify-between hover:shadow-md transition-all group">
          <div className="flex justify-between items-start">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Upcoming</span>
            <div className="p-2 bg-slate-50 text-slate-500 rounded-lg group-hover:bg-indigo-50 group-hover:text-indigo-650 transition-colors">
              <Calendar className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-4">
            <span className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">{upcomingCount}</span>
            <div className="text-slate-400 text-[10px] font-semibold mt-1">My registered events</div>
          </div>
        </div>

        {/* Active Passes */}
        <div className="bg-white p-5 rounded-xl border border-slate-150 shadow-xs flex flex-col justify-between hover:shadow-md transition-all group">
          <div className="flex justify-between items-start">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Active Passes</span>
            <div className="p-2 bg-emerald-50 text-emerald-650 rounded-lg group-hover:bg-emerald-100 group-hover:text-emerald-700 transition-colors">
              <Ticket className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-4">
            <span className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">{activeTicketsCount}</span>
            <div className="text-emerald-650 text-[10px] font-bold mt-1">Valid for check-in</div>
          </div>
        </div>

        {/* Checked In */}
        <div className="bg-white p-5 rounded-xl border border-slate-150 shadow-xs flex flex-col justify-between hover:shadow-md transition-all group">
          <div className="flex justify-between items-start">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Checked In</span>
            <div className="p-2 bg-slate-50 text-slate-500 rounded-lg group-hover:bg-indigo-50 group-hover:text-indigo-650 transition-colors">
              <CheckCircle className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-4">
            <span className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">{checkedInCount}</span>
            <div className="text-slate-400 text-[10px] font-semibold mt-1">Check-ins completed</div>
          </div>
        </div>

        {/* Available Summits */}
        <div className="bg-white p-5 rounded-xl border border-slate-150 shadow-xs flex flex-col justify-between hover:shadow-md transition-all group">
          <div className="flex justify-between items-start">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Discovery</span>
            <div className="p-2 bg-indigo-50 text-indigo-650 rounded-lg group-hover:bg-indigo-100 group-hover:text-indigo-700 transition-colors">
              <Compass className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-4">
            <span className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">{availableCount}</span>
            <div className="text-indigo-650 text-[10px] font-bold mt-1">Available events</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Upcoming Events Column (2/3 width) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-base font-bold text-slate-900 tracking-tight">Your Upcoming Schedule</h3>
            {upcomingEvents.length > 0 && (
              <Link to="/portal/events" className="text-xs font-bold text-indigo-600 hover:text-indigo-800 transition-colors flex items-center space-x-0.5">
                <span>View All</span>
                <ChevronRight className="h-3.5 w-3.5" />
              </Link>
            )}
          </div>

          {upcomingEvents.length === 0 ? (
            <div className="text-center py-12 bg-white border border-slate-150 rounded-xl shadow-xs flex flex-col items-center justify-center p-6">
              <div className="p-3 bg-slate-50 rounded-full text-slate-400 mb-3.5">
                <Calendar className="h-7 w-7" />
              </div>
              <h4 className="text-sm font-bold text-slate-900 tracking-tight">No Upcoming Bookings</h4>
              <p className="text-xs text-slate-500 mt-1 max-w-xs font-medium">
                You haven't reserved tickets for any upcoming events.
              </p>
              <Link
                to="/portal/events/available"
                className="mt-4 px-4 py-2 bg-indigo-600 hover:bg-indigo-755 text-white rounded-xl text-xs font-bold transition-all shadow-xs cursor-pointer"
              >
                Browse Available Events
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {upcomingEvents.slice(0, 3).map(e => (
                <div key={e.id} className="bg-white rounded-xl border border-slate-150 p-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 hover:shadow-md transition-all">
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <h4 className="text-sm font-bold text-slate-850 line-clamp-1 leading-snug">{e.name}</h4>
                      <span className={`inline-block text-[8px] px-1.5 py-0.5 border rounded-full font-bold uppercase tracking-wider ${
                        e.checked_in 
                          ? 'bg-green-50 text-green-700 border-green-200' 
                          : 'bg-slate-50 text-slate-600 border-slate-200'
                      }`}>
                        {e.checked_in ? '✓ In Gate' : 'Awaiting Gate'}
                      </span>
                    </div>

                    <div className="flex flex-wrap gap-4 text-xs font-semibold text-slate-450">
                      <div className="flex items-center space-x-1">
                        <Calendar className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                        <span>{e.date}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Clock className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                        <span>{e.start_time} - {e.end_time}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <MapPin className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                        <span>{e.venue}</span>
                      </div>
                    </div>
                  </div>

                  <Link
                    to={`/portal/events/${e.id}`}
                    className="text-xs font-bold text-slate-600 hover:text-indigo-600 border border-slate-200 hover:border-indigo-100 bg-slate-50 hover:bg-indigo-50 px-3.5 py-1.5 rounded-lg transition-all self-stretch sm:self-auto text-center shrink-0 cursor-pointer"
                  >
                    Details
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* My Active Passes Column (1/3 width) */}
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-base font-bold text-slate-900 tracking-tight">Active Passes</h3>
            {activeTicketsCount > 0 && (
              <Link to="/portal/tickets" className="text-xs font-bold text-indigo-600 hover:text-indigo-800 transition-colors flex items-center space-x-0.5">
                <span>All Passes</span>
                <ChevronRight className="h-3.5 w-3.5" />
              </Link>
            )}
          </div>

          {events.filter(e => e.ticket_status === 'active').length === 0 ? (
            <div className="bg-white border border-slate-150 p-6 rounded-xl text-center text-slate-400 text-xs italic font-medium py-12">
              No active check-in passes.
            </div>
          ) : (
            <div className="space-y-4">
              {events
                .filter(e => e.ticket_status === 'active')
                .slice(0, 3)
                .map(e => (
                  <div key={e.id} className="bg-slate-950 text-white rounded-xl border border-slate-850 p-5 flex flex-col justify-between space-y-4 shadow-xl">
                    <div className="space-y-1.5">
                      <div className="flex justify-between items-center">
                        <span className="text-[9px] font-black text-indigo-400 tracking-widest uppercase">Digital Stub</span>
                        <span className="font-mono text-[9px] font-bold text-slate-400 uppercase select-all tracking-wider">
                          {e.ticket_code}
                        </span>
                      </div>
                      <h4 className="text-xs font-extrabold text-slate-100 line-clamp-1">{e.name}</h4>
                      <p className="text-[10px] text-slate-400 font-semibold">{e.date} &bull; {e.venue}</p>
                    </div>
                    
                    {/* View pass stub button */}
                    <button
                      onClick={async () => {
                        // find ticket ID matching ticket_code
                        try {
                          const resTkt = await api.get('/api/portal/tickets');
                          const target = resTkt.data.data.find(t => t.ticket_code === e.ticket_code);
                          if (target) navigate(`/portal/tickets/${target.id}`);
                        } catch (err) {
                          console.error(err);
                        }
                      }}
                      className="w-full text-center py-2 bg-indigo-600 hover:bg-indigo-755 text-white rounded-lg text-[11px] font-bold transition-all shadow-xs cursor-pointer"
                    >
                      View Pass
                    </button>
                  </div>
                ))}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
