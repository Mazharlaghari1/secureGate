import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../../services/api';
import {
  ArrowLeft,
  Calendar,
  MapPin,
  Clock,
  Ticket,
  CheckCircle,
  XCircle,
  HelpCircle,
  ShieldCheck,
  FileText,
  AlertTriangle,
  Info
} from 'lucide-react';

export default function AvailableEventDetails() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Booking states
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingError, setBookingError] = useState('');
  const [bookingSuccess, setBookingSuccess] = useState(null);

  const fetchEventDetails = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/api/portal/events/available/${id}`);
      setData(res.data.data);
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to load event details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEventDetails();
  }, [id]);

  const handleBookTicket = async () => {
    setBookingLoading(true);
    setBookingError('');
    try {
      const res = await api.post(`/api/portal/events/${id}/book`);
      setBookingSuccess(res.data.data.ticket);
      // Reload event details
      await fetchEventDetails();
    } catch (err) {
      setBookingError(err.response?.data?.error?.message || 'Booking failed.');
    } finally {
      setBookingLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 max-w-4xl mx-auto space-y-6 animate-pulse">
        <div className="h-6 bg-slate-200 rounded w-1/6"></div>
        <div className="h-10 bg-slate-200 rounded w-1/3"></div>
        <div className="h-32 bg-slate-200 rounded-xl"></div>
        <div className="h-48 bg-slate-200 rounded-xl"></div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8 max-w-xl mx-auto text-center space-y-4">
        <div className="bg-red-50 text-red-700 p-4 rounded-xl border border-red-200 font-semibold text-sm">
          {error || 'Unable to retrieve details for this event.'}
        </div>
        <Link to="/portal/events/available" className="inline-block text-sm font-bold text-indigo-650 hover:underline">
          &larr; Back to Available Events
        </Link>
      </div>
    );
  }

  const { name, venue, date, start_time, end_time, timezone, description, capacity, registered_count, remaining_capacity, booking_open, already_booked, ticket_id } = data;
  const isSoldOut = remaining_capacity === 0;

  return (
    <div className="p-6 md:p-8 max-w-4xl mx-auto space-y-6 relative">
      
      {/* Back link */}
      <div>
        <Link 
          to="/portal/events/available"
          className="inline-flex items-center space-x-2 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Available Events</span>
        </Link>
      </div>

      {/* Main Info Card */}
      <div className="bg-white rounded-xl border border-slate-150 shadow-xs p-6">
        <div className="pb-6 border-b border-slate-100 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[9px] px-2.5 py-0.5 bg-green-50 text-green-700 border border-green-200 rounded-full font-bold uppercase tracking-wider">
                Booking Open
              </span>
              <span className="text-xs text-slate-400 font-medium font-mono">Discovery Portal</span>
            </div>
            <h1 className="text-xl md:text-2xl font-extrabold text-slate-900 mt-2.5 tracking-tight">{name}</h1>
          </div>

          <div className="shrink-0 w-full sm:w-auto">
            {already_booked ? (
              <Link
                to={ticket_id ? `/portal/tickets/${ticket_id}` : "/portal/tickets"}
                className="w-full text-center py-2.5 px-6 bg-indigo-50 hover:bg-indigo-100 text-indigo-750 border border-indigo-200 rounded-xl text-xs font-bold transition-all shadow-xs block cursor-pointer"
              >
                View My Ticket Pass
              </Link>
            ) : isSoldOut ? (
              <button
                disabled
                className="w-full py-2.5 px-6 bg-slate-200 text-slate-400 border border-slate-250 rounded-xl text-xs font-bold cursor-not-allowed"
              >
                Sold Out
              </button>
            ) : (
              <button
                onClick={() => setConfirmOpen(true)}
                className="w-full py-2.5 px-6 bg-indigo-600 hover:bg-indigo-755 text-white rounded-xl text-xs font-bold transition-all shadow-md shadow-indigo-600/10 cursor-pointer"
              >
                Book My Ticket
              </button>
            )}
          </div>
        </div>

        {/* Details Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 pt-6 text-xs text-slate-500 font-semibold">
          <div className="space-y-1">
            <span className="text-[10px] text-slate-444 uppercase tracking-wider block">Location</span>
            <div className="flex items-center space-x-1.5 text-slate-800">
              <MapPin className="h-4 w-4 text-slate-400 shrink-0" />
              <span className="truncate">{venue}</span>
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-[10px] text-slate-444 uppercase tracking-wider block">Scheduled Date</span>
            <div className="flex items-center space-x-1.5 text-slate-800">
              <Calendar className="h-4 w-4 text-slate-400 shrink-0" />
              <span>{date}</span>
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-[10px] text-slate-444 uppercase tracking-wider block">Timings</span>
            <div className="flex items-center space-x-1.5 text-slate-800">
              <Clock className="h-4 w-4 text-slate-400 shrink-0" />
              <span>{start_time} - {end_time} ({timezone})</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Description */}
        <div className="md:col-span-2 bg-white rounded-xl border border-slate-150 p-6 space-y-4 shadow-xs">
          <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center space-x-1.5 border-b border-slate-50 pb-3">
            <FileText className="h-4 w-4 text-slate-450" />
            <span>Summit Agenda & Detail</span>
          </h3>
          <p className="text-slate-600 text-sm leading-relaxed whitespace-pre-wrap font-medium">
            {description || 'No agenda details provided for this event.'}
          </p>
        </div>

        {/* Capacity / Reservation status */}
        <div className="bg-white rounded-xl border border-slate-150 p-6 space-y-4 shadow-xs flex flex-col justify-between">
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center space-x-1.5 border-b border-slate-50 pb-3">
              <Ticket className="h-4 w-4 text-slate-450" />
              <span>Seats & Availability</span>
            </h3>

            <div className="space-y-3 text-xs font-semibold text-slate-500">
              <div className="flex justify-between items-center">
                <span>Total Seats:</span>
                <span className="text-slate-800">{capacity}</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Seats Booked:</span>
                <span className="text-slate-800">{registered_count}</span>
              </div>
              <div className="flex justify-between items-center border-t border-slate-100 pt-3">
                <span>Seats Left:</span>
                {isSoldOut ? (
                  <span className="text-red-650 font-bold">Sold Out</span>
                ) : (
                  <span className="text-indigo-650 font-bold">{remaining_capacity}</span>
                )}
              </div>
            </div>
          </div>

          {!already_booked && !isSoldOut && (
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-150 text-[10px] text-slate-450 leading-relaxed font-semibold">
              Note: One reservation pass is permitted per attendee email.
            </div>
          )}
        </div>
      </div>

      {/* Confirmation Modal */}
      {confirmOpen && !bookingSuccess && (
        <div className="fixed inset-0 bg-slate-950/70 z-50 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="bg-white rounded-2xl border border-slate-150 max-w-sm w-full p-6 space-y-5 shadow-2xl animate-in fade-in zoom-in duration-200">
            <div>
              <h3 className="text-base font-extrabold text-slate-900 tracking-tight">Reserve your place?</h3>
              <p className="text-xs text-slate-550 mt-1 font-medium font-sans">You are about to register for this event.</p>
            </div>

            <div className="bg-slate-50 p-4 rounded-xl border border-slate-150 space-y-2 text-xs font-semibold text-slate-500">
              <p className="text-slate-800 font-extrabold">{name}</p>
              <div className="flex items-center space-x-1.5">
                <Calendar className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                <span>{date}</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <MapPin className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                <span>{venue}</span>
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
                onClick={() => setConfirmOpen(false)}
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
              <p className="text-xs text-slate-550 font-medium">Your ticket has been created successfully.</p>
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
                  setConfirmOpen(false);
                }}
                className="w-full text-center py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-bold transition-all cursor-pointer"
              >
                Back to Event Details
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
