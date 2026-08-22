import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../../services/api';
import {
  Calendar,
  MapPin,
  Clock,
  Search,
  SlidersHorizontal,
  RefreshCw,
  Compass,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Ticket,
  Info
} from 'lucide-react';

export default function AvailableEvents() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterOption, setFilterOption] = useState('all'); // 'all' | 'available' | 'almost_full' | 'sold_out'

  // Booking states
  const [bookingEvent, setBookingEvent] = useState(null); // Event currently trying to book
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingError, setBookingError] = useState('');
  const [bookingSuccess, setBookingSuccess] = useState(null); // Success ticket payload

  const fetchAvailableEvents = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/portal/events/available');
      setEvents(res.data.data);
    } catch (err) {
      console.error('Failed to fetch available events:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAvailableEvents();
  }, []);

  const handleBookTicket = async () => {
    if (!bookingEvent) return;
    setBookingLoading(true);
    setBookingError('');
    try {
      const res = await api.post(`/api/portal/events/${bookingEvent.id}/book`);
      setBookingSuccess(res.data.data.ticket);
      // Refresh event list to update seat capacities
      await fetchAvailableEvents();
    } catch (err) {
      setBookingError(err.response?.data?.error?.message || 'Booking failed.');
    } finally {
      setBookingLoading(false);
    }
  };

  const filteredEvents = events.filter(e => {
    const matchesSearch = e.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          e.venue.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          (e.description && e.description.toLowerCase().includes(searchQuery.toLowerCase()));

    if (filterOption === 'available') {
      return matchesSearch && e.booking_open && !e.already_booked;
    }
    if (filterOption === 'almost_full') {
      return matchesSearch && e.remaining_capacity > 0 && e.remaining_capacity <= 10;
    }
    if (filterOption === 'sold_out') {
      return matchesSearch && e.remaining_capacity === 0;
    }
    return matchesSearch;
  });

  return (
    <div className="p-6 md:p-8 max-w-6xl mx-auto space-y-6 relative">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">Available Events</h1>
          <p className="text-slate-500 text-sm mt-0.5 font-medium font-sans">
            Discover upcoming events and reserve your place.
          </p>
        </div>
        <button
          onClick={fetchAvailableEvents}
          className="flex items-center space-x-2 px-3.5 py-2 bg-white hover:bg-slate-50 text-slate-700 hover:text-slate-900 border border-slate-200 rounded-lg text-xs font-bold transition-all shadow-xs cursor-pointer shrink-0"
        >
          <RefreshCw className="h-3.5 w-3.5 text-slate-450" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between bg-white p-4 rounded-xl border border-slate-150 shadow-xs">
        {/* Search */}
        <div className="relative w-full sm:max-w-xs">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search summits or venues..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-slate-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-lg text-sm focus:outline-none transition-all placeholder-slate-400 bg-slate-50/50"
          />
        </div>

        {/* Filter selection */}
        <div className="flex items-center space-x-2 text-xs font-semibold text-slate-555 w-full sm:w-auto">
          <SlidersHorizontal className="h-3.5 w-3.5 text-slate-400" />
          <span>Availability:</span>
          <select
            value={filterOption}
            onChange={(e) => setFilterOption(e.target.value)}
            className="px-2.5 py-1.5 border border-slate-200 bg-slate-50 rounded-lg focus:outline-none text-xs font-bold text-slate-700 cursor-pointer"
          >
            <option value="all">All Events</option>
            <option value="available">Bookable (Open)</option>
            <option value="almost_full">Almost Full</option>
            <option value="sold_out">Sold Out</option>
          </select>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-pulse">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-56 bg-slate-200 rounded-xl"></div>
          ))}
        </div>
      ) : filteredEvents.length === 0 ? (
        <div className="text-center py-16 bg-white border border-slate-150 rounded-xl shadow-xs flex flex-col items-center justify-center p-6">
          <div className="p-3 bg-slate-50 rounded-full text-slate-400 mb-3">
            <Compass className="h-8 w-8" />
          </div>
          <h3 className="text-sm font-bold text-slate-900 tracking-tight">No events available right now.</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm font-medium">
            Check back later for newly published summits and seminars.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {filteredEvents.map(e => {
            const isSoldOut = e.remaining_capacity === 0;
            const isAlmostFull = e.remaining_capacity > 0 && e.remaining_capacity <= 10;
            return (
              <div key={e.id} className="bg-white rounded-xl border border-slate-150 shadow-xs flex flex-col justify-between hover:shadow-md transition-all overflow-hidden">
                <div className="p-5 space-y-4">
                  <div className="space-y-1">
                    <h4 className="text-sm font-extrabold text-slate-850 line-clamp-1 leading-snug">{e.name}</h4>
                    <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed font-medium">
                      {e.description || 'No description provided.'}
                    </p>
                  </div>

                  <div className="space-y-2 text-xs font-semibold text-slate-450 border-t border-slate-50 pt-3">
                    <div className="flex items-center space-x-1.5">
                      <Calendar className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                      <span>{e.date}</span>
                    </div>
                    <div className="flex items-center space-x-1.5">
                      <Clock className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                      <span>{e.start_time} - {e.end_time}</span>
                    </div>
                    <div className="flex items-center space-x-1.5">
                      <MapPin className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                      <span className="truncate">{e.venue}</span>
                    </div>
                  </div>

                  {/* Capacity indicator */}
                  <div className="pt-2 flex items-center">
                    {isSoldOut ? (
                      <span className="inline-flex items-center space-x-1 text-[9px] px-2.5 py-0.5 bg-red-50 text-red-700 border border-red-100 rounded-full font-bold uppercase">
                        <XCircle className="h-3 w-3 shrink-0" />
                        <span>Sold Out</span>
                      </span>
                    ) : isAlmostFull ? (
                      <span className="inline-flex items-center space-x-1 text-[9px] px-2.5 py-0.5 bg-amber-50 text-amber-700 border border-amber-100 rounded-full font-bold uppercase">
                        <AlertTriangle className="h-3 w-3 shrink-0" />
                        <span>Almost Full ({e.remaining_capacity} left)</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center space-x-1 text-[9px] px-2.5 py-0.5 bg-indigo-50 text-indigo-700 border border-indigo-100 rounded-full font-bold uppercase">
                        <Info className="h-3 w-3 shrink-0" />
                        <span>{e.remaining_capacity} seats remaining</span>
                      </span>
                    )}
                  </div>
                </div>

                <div className="bg-slate-50 p-4 border-t border-slate-100 flex items-center space-x-2">
                  <Link
                    to={`/portal/events/available/${e.id}`}
                    className="flex-1 text-center py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-lg text-xs font-bold transition-all shadow-xs cursor-pointer block"
                  >
                    View Details
                  </Link>

                  {e.already_booked ? (
                    <Link
                      to="/portal/tickets"
                      className="flex-1 text-center py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 rounded-lg text-xs font-bold transition-all cursor-pointer block"
                    >
                      View Ticket
                    </Link>
                  ) : isSoldOut ? (
                    <button
                      disabled
                      className="flex-1 py-2 bg-slate-200 text-slate-400 rounded-lg text-xs font-bold cursor-not-allowed border border-slate-250"
                    >
                      Sold Out
                    </button>
                  ) : (
                    <button
                      onClick={() => setBookingEvent(e)}
                      className="flex-1 py-2 bg-indigo-600 hover:bg-indigo-755 text-white rounded-lg text-xs font-bold transition-all shadow-xs cursor-pointer"
                    >
                      Book Ticket
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Confirmation Modal */}
      {bookingEvent && !bookingSuccess && (
        <div className="fixed inset-0 bg-slate-950/70 z-50 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="bg-white rounded-2xl border border-slate-150 max-w-sm w-full p-6 space-y-5 shadow-2xl animate-in fade-in zoom-in duration-200">
            <div>
              <h3 className="text-base font-extrabold text-slate-900 tracking-tight">Reserve your place?</h3>
              <p className="text-xs text-slate-550 mt-1 font-medium font-sans">You are about to register for this event.</p>
            </div>

            <div className="bg-slate-50 p-4 rounded-xl border border-slate-150 space-y-2 text-xs font-semibold text-slate-500">
              <p className="text-slate-800 font-extrabold">{bookingEvent.name}</p>
              <div className="flex items-center space-x-1.5">
                <Calendar className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                <span>{bookingEvent.date}</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <MapPin className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                <span>{bookingEvent.venue}</span>
              </div>
            </div>

            {bookingError && (
              <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg text-xs font-semibold flex items-center space-x-1.5">
                <AlertTriangle className="h-4 w-4 text-red-500 shrink-0" />
                <span>{bookingError}</span>
              </div>
            )}

            <div className="flex items-center justify-end space-x-2 pt-2">
              <button
                disabled={bookingLoading}
                onClick={() => setBookingEvent(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-bold transition-all cursor-pointer"
              >
                Cancel
              </button>
              <button
                disabled={bookingLoading}
                onClick={handleBookTicket}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-755 text-white rounded-lg text-xs font-bold transition-all shadow-xs cursor-pointer disabled:opacity-50"
              >
                {bookingLoading ? 'Booking...' : 'Confirm Booking'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Success Modal */}
      {bookingSuccess && (
        <div className="fixed inset-0 bg-slate-950/70 z-50 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="bg-white rounded-2xl border border-slate-150 max-w-sm w-full p-6 text-center space-y-6 shadow-2xl animate-in fade-in zoom-in duration-200">
            <div className="mx-auto h-12 w-12 bg-emerald-50 rounded-full flex items-center justify-center border border-emerald-100 text-emerald-600">
              <CheckCircle className="h-6 w-6" />
            </div>

            <div className="space-y-1.5">
              <h3 className="text-base font-extrabold text-slate-900 tracking-tight">✓ Booking Confirmed</h3>
              <p className="text-xs text-slate-500 font-medium">Your ticket has been created successfully.</p>
            </div>

            <div className="bg-slate-50 p-4 rounded-xl border border-slate-150 text-xs font-semibold text-slate-500 space-y-2">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Ticket Code</span>
              <span className="font-mono text-sm bg-indigo-50 border border-indigo-100 text-indigo-700 px-3 py-1 rounded font-extrabold select-all tracking-wider inline-block">
                {bookingSuccess.ticket_code}
              </span>
            </div>

            <div className="flex flex-col gap-2 pt-2">
              <Link
                to={`/portal/tickets/${bookingSuccess.id}`}
                className="w-full text-center py-2 bg-indigo-600 hover:bg-indigo-755 text-white rounded-lg text-xs font-bold transition-all shadow-xs block"
              >
                View My Ticket Pass
              </Link>
              <button
                onClick={() => {
                  setBookingSuccess(null);
                  setBookingEvent(null);
                }}
                className="w-full text-center py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-bold transition-all cursor-pointer"
              >
                Back to Available Events
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
