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
  FileText
} from 'lucide-react';

export default function PortalEventDetails() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchEventDetails = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/api/portal/events/${id}`);
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
        <Link to="/portal/events" className="inline-block text-sm font-bold text-indigo-650 hover:underline">
          &larr; Back to My Events
        </Link>
      </div>
    );
  }

  const { event, ticket_id, ticket_code, ticket_status, checked_in, scanned_at } = data;

  return (
    <div className="p-6 md:p-8 max-w-4xl mx-auto space-y-6">
      
      {/* Back link */}
      <div>
        <Link 
          to="/portal/events"
          className="inline-flex items-center space-x-2 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to My Events</span>
        </Link>
      </div>

      {/* Event Info Card */}
      <div className="bg-white rounded-xl border border-slate-150 shadow-xs p-6">
        <div className="pb-6 border-b border-slate-100">
          <div className="flex items-center space-x-2">
            <span className={`text-[9px] px-2.5 py-0.5 border rounded-full font-bold uppercase tracking-wider ${
              event.status === 'active' ? 'bg-green-50 text-green-700 border-green-200' :
              event.status === 'completed' ? 'bg-blue-50 text-blue-700 border-blue-200' :
              'bg-slate-50 text-slate-650 border-slate-200'
            }`}>
              {event.status === 'active' ? 'published' : event.status}
            </span>
            <span className="text-xs text-slate-400 font-medium">Event Information</span>
          </div>
          <h1 className="text-xl md:text-2xl font-extrabold text-slate-900 mt-2.5 tracking-tight">{event.name}</h1>
        </div>

        {/* Schedule/Location details grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 pt-6 text-xs text-slate-500 font-semibold">
          <div className="space-y-1">
            <span className="text-[10px] text-slate-450 uppercase tracking-wider block">Venue</span>
            <div className="flex items-center space-x-1.5 text-slate-800">
              <MapPin className="h-4 w-4 text-slate-400 shrink-0" />
              <span className="truncate">{event.venue}</span>
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-[10px] text-slate-450 uppercase tracking-wider block">Date</span>
            <div className="flex items-center space-x-1.5 text-slate-800">
              <Calendar className="h-4 w-4 text-slate-400 shrink-0" />
              <span>{event.date}</span>
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-[10px] text-slate-450 uppercase tracking-wider block">Time</span>
            <div className="flex items-center space-x-1.5 text-slate-800">
              <Clock className="h-4 w-4 text-slate-400 shrink-0" />
              <span>{event.start_time} - {event.end_time} ({event.timezone})</span>
            </div>
          </div>
        </div>
      </div>

      {/* Event description and access details */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Description (2/3 width) */}
        <div className="md:col-span-2 bg-white rounded-xl border border-slate-150 shadow-xs p-6 space-y-4">
          <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center space-x-1.5 border-b border-slate-50 pb-3">
            <FileText className="h-4 w-4 text-slate-450" />
            <span>Description</span>
          </h3>
          <p className="text-slate-600 text-sm leading-relaxed whitespace-pre-wrap font-medium">
            {event.description || 'No description provided for this event.'}
          </p>
        </div>

        {/* Access Ticket Stub (1/3 width) */}
        <div className="bg-white rounded-xl border border-slate-150 shadow-xs p-6 flex flex-col justify-between">
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center space-x-1.5 border-b border-slate-50 pb-3">
              <Ticket className="h-4 w-4 text-slate-450" />
              <span>Your Access Stub</span>
            </h3>

            {ticket_code ? (
              <div className="space-y-4">
                <div>
                  <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Ticket Code</span>
                  <span className="font-mono text-sm bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded border border-indigo-100 font-extrabold select-all tracking-wider inline-block mt-1">
                    {ticket_code}
                  </span>
                </div>

                <div>
                  <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Ticket Status</span>
                  <span className={`inline-block text-[10px] px-2.5 py-0.5 border rounded-full font-bold uppercase mt-1 ${
                    ticket_status === 'active' ? 'bg-green-50 text-green-700 border-green-200' :
                    ticket_status === 'used' ? 'bg-indigo-50 text-indigo-700 border-indigo-200' :
                    'bg-red-50 text-red-700 border-red-200'
                  }`}>
                    {ticket_status}
                  </span>
                </div>

                <div>
                  <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Check-in Status</span>
                  <span className={`inline-block text-[10px] px-2.5 py-0.5 border rounded-full font-bold uppercase mt-1 ${
                    checked_in ? 'bg-green-50 text-green-700 border-green-200' : 'bg-slate-50 text-slate-655 border-slate-200'
                  }`}>
                    {checked_in ? '✓ Checked in' : 'Not checked in'}
                  </span>
                  {checked_in && scanned_at && (
                    <p className="text-[10px] text-slate-450 mt-1 font-mono">
                      Checked in at: {new Date(scanned_at).toLocaleTimeString()}
                    </p>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center py-6 text-slate-400 text-xs italic">
                No ticket code has been generated for you yet. Check back closer to the event schedule.
              </div>
            )}
          </div>

          {ticket_id && (
            <Link
              to={`/portal/tickets/${ticket_id}`}
              className="mt-6 w-full text-center py-2 bg-slate-900 hover:bg-slate-950 text-white rounded-lg text-xs font-bold transition-all shadow-xs cursor-pointer"
            >
              View QR Ticket Pass &rarr;
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
