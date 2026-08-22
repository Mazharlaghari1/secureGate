import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../../services/api';
import {
  ShieldCheck,
  Calendar,
  MapPin,
  Clock,
  User,
  Ticket,
  AlertTriangle,
  QrCode,
  XCircle,
  HelpCircle,
  Download
} from 'lucide-react';

export default function PublicTicket() {
  const { token } = useParams();
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchTicket = async () => {
      try {
        const res = await api.get(`/api/tickets/${token}`);
        setTicket(res.data.data);
      } catch (err) {
        setError(err.response?.data?.error?.message || 'Ticket could not be retrieved.');
      } finally {
        setLoading(false);
      }
    };
    fetchTicket();
  }, [token]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-slate-950 text-white">
        <div className="flex items-center space-x-2 text-slate-450 text-sm font-semibold">
          <svg className="animate-spin h-5 w-5 text-indigo-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span>Fetching event pass credentials...</span>
        </div>
      </div>
    );
  }

  if (error || !ticket) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-slate-950">
        <div className="bg-slate-900 p-8 rounded-2xl shadow-2xl max-w-sm w-full text-center border border-slate-850 text-white space-y-4">
          <div className="p-3 bg-red-950/20 text-red-500 rounded-full inline-block border border-red-900/30">
            <AlertTriangle className="h-8 w-8" />
          </div>
          <h2 className="text-xl font-bold text-slate-200">Invalid Event Pass</h2>
          <p className="text-slate-450 text-xs font-medium leading-relaxed">
            {error || 'This digital ticket link is invalid, has expired, or was revoked by administrators.'}
          </p>
        </div>
      </div>
    );
  }

  const isTicketActive = ticket.status === 'active';

  const getStatusStyle = (status) => {
    switch (status) {
      case 'active':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'used':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      case 'revoked':
        return 'bg-red-50 text-red-705 border-red-200';
      default:
        return 'bg-slate-50 text-slate-600 border-slate-200';
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'active':
        return 'Access Permitted';
      case 'used':
        return 'Already Checked In';
      case 'revoked':
        return 'Ticket Revoked';
      default:
        return status.toUpperCase();
    }
  };

  // Generate QR code using public API
  const qrCodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent(ticket.qr_payload)}`;

  return (
    <div className="min-h-screen bg-slate-950 py-12 px-4 flex flex-col items-center justify-center relative overflow-hidden">
      
      {/* Abstract backdrop mesh */}
      <div className="absolute inset-0 opacity-5 pointer-events-none">
        <div className="absolute inset-0" style={{
          backgroundImage: 'radial-gradient(circle, #4F46E5 1px, transparent 1px)',
          backgroundSize: '20px 20px'
        }}></div>
      </div>

      <div className="w-full max-w-sm relative z-10 flex flex-col items-center">
        {/* Top brand header */}
        <div className="flex items-center space-x-2.5 mb-6 text-white">
          <ShieldCheck className="h-6 w-6 text-indigo-500" />
          <span className="font-extrabold text-base tracking-tight select-none">SecureGate Event Pass</span>
        </div>

        {/* Premium Digital Ticket Pass card layout */}
        <div className="bg-white rounded-2xl shadow-2xl w-full overflow-hidden border border-slate-150 flex flex-col relative">
          
          {/* Top section: Event Details stub */}
          <div className="bg-slate-900 p-6 text-white text-center relative">
            <h1 className="text-lg font-extrabold tracking-tight line-clamp-1">{ticket.event.name}</h1>
            <p className="text-slate-400 text-xs mt-1.5 font-medium flex items-center justify-center space-x-1">
              <MapPin className="h-3.5 w-3.5 text-slate-500" />
              <span>{ticket.event.venue}</span>
            </p>
          </div>

          {/* Ticket punch-out stub side notches with dashed divider line */}
          <div className="relative h-6 bg-white flex items-center justify-between">
            <div className="absolute -left-3 h-6 w-6 rounded-full bg-slate-950 border-r border-slate-150"></div>
            <div className="w-full border-t border-dashed border-slate-200 mx-5"></div>
            <div className="absolute -right-3 h-6 w-6 rounded-full bg-slate-950 border-l border-slate-150"></div>
          </div>

          {/* Bottom section: QR holder & Details */}
          <div className="p-6 flex flex-col items-center bg-white">
            
            {/* Status Indicator */}
            <span className={`px-3.5 py-1 border rounded-full text-xs font-bold uppercase tracking-wider mb-5 ${getStatusStyle(ticket.status)}`}>
              {getStatusLabel(ticket.status)}
            </span>

            {/* QR Viewport */}
            {isTicketActive ? (
              <div className="bg-slate-50 p-4 rounded-2xl border border-slate-150 shadow-inner flex flex-col items-center mb-6 relative group">
                <img
                  src={qrCodeUrl}
                  alt="Secure QR Pass code"
                  className="w-52 h-52 object-contain"
                />
                <div className="flex items-center space-x-1.5 text-[10px] text-slate-450 mt-3 font-semibold">
                  <QrCode className="h-3.5 w-3.5" />
                  <span>Present barcode at entrance check-in</span>
                </div>
              </div>
            ) : (
              <div className="bg-slate-50 w-52 h-52 rounded-2xl border border-slate-150 flex flex-col items-center justify-center mb-6 text-center p-4">
                <XCircle className="h-10 w-10 text-red-500 mb-2 animate-pulse" />
                <p className="text-xs font-bold text-slate-800 uppercase tracking-tight">QR Code Disabled</p>
                <p className="text-[10px] text-slate-450 mt-1 max-w-[140px] font-medium leading-relaxed">
                  This passcode cannot be checked in at gate entrance.
                </p>
              </div>
            )}

            {/* Attendee Details list */}
            <div className="w-full space-y-3.5 border-t border-slate-100 pt-5 text-xs text-slate-500 font-semibold">
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Attendee:</span>
                <span className="font-bold text-slate-800">{ticket.participant.name}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Ticket Code:</span>
                <span className="font-mono text-xs font-bold bg-indigo-50 border border-indigo-100 text-indigo-700 px-2 py-0.5 rounded select-all tracking-wider">
                  {ticket.ticket_code}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Date:</span>
                <span className="text-slate-800">{ticket.event.date}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Time Bounds:</span>
                <span className="text-slate-800">{ticket.event.start_time} - {ticket.event.end_time}</span>
              </div>
              <div className="flex justify-between items-center border-t border-slate-100 pt-3">
                <span className="text-slate-400">Valid Until:</span>
                <span className="text-slate-700 font-mono text-[10px]">
                  {new Date(ticket.expires_at).toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer brand indicator */}
        <span className="text-[10px] font-bold text-slate-600 mt-6 tracking-widest uppercase select-none">
          CRYPTOGRAPHIC GATE ENTRY NODE
        </span>
      </div>
    </div>
  );
}
