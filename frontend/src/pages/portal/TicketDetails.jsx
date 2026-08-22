import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../../services/api';
import {
  ArrowLeft,
  Calendar,
  MapPin,
  Clock,
  User,
  Ticket,
  AlertTriangle,
  QrCode,
  XCircle,
  CheckCircle,
  RefreshCw
} from 'lucide-react';

export default function PortalTicketDetails() {
  const { id } = useParams();
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Rotating QR states
  const [qrToken, setQrToken] = useState('');
  const [countdown, setCountdown] = useState(60);
  const [qrError, setQrError] = useState('');
  
  const timerRef = useRef(null);
  const pollRef = useRef(null);

  const fetchTicketStatus = async () => {
    try {
      const res = await api.get(`/api/portal/tickets/${id}`);
      setTicket(res.data.data);
      if (res.data.data.status === 'used') {
        // Stop QR token refresh and timers
        clearTimers();
      }
    } catch (err) {
      console.error('Failed to poll ticket status:', err);
    }
  };

  const fetchQrToken = async () => {
    try {
      const res = await api.get(`/api/portal/tickets/${id}/qr`);
      setQrToken(res.data.data.qr_token);
      setCountdown(60);
      setQrError('');
    } catch (err) {
      setQrError(err.response?.data?.error?.message || 'Failed to fetch security code.');
    }
  };

  const clearTimers = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (pollRef.current) clearInterval(pollRef.current);
  };

  const fetchInitialData = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get(`/api/portal/tickets/${id}`);
      setTicket(res.data.data);
      
      if (res.data.data.status === 'active') {
        // Fetch first QR token
        const qrRes = await api.get(`/api/portal/tickets/${id}/qr`);
        setQrToken(qrRes.data.data.qr_token);
        setCountdown(60);
        
        // Start timers
        clearTimers();
        
        // Countdown timer
        timerRef.current = setInterval(() => {
          setCountdown(prev => {
            if (prev <= 6) {
              // Fetch a new QR before it expires (around 55 seconds elapsed)
              fetchQrToken();
              return 60;
            }
            return prev - 1;
          });
        }, 1000);

        // Polling timer for status check (every 5 seconds)
        pollRef.current = setInterval(fetchTicketStatus, 5000);
      }
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Ticket could not be retrieved.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInitialData();
    return () => clearTimers();
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center p-4">
        <div className="flex items-center space-x-2 text-slate-450 text-xs font-semibold animate-pulse">
          <svg className="animate-spin h-5 w-5 text-indigo-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span>Fetching secure pass ticket...</span>
        </div>
      </div>
    );
  }

  if (error || !ticket) {
    return (
      <div className="p-8 max-w-sm mx-auto text-center space-y-4">
        <div className="bg-red-50 text-red-700 p-4 rounded-xl border border-red-200 font-semibold text-sm">
          {error || 'This ticket details could not be loaded.'}
        </div>
        <Link to="/portal/tickets" className="inline-block text-sm font-bold text-indigo-650 hover:underline">
          &larr; Back to My Tickets
        </Link>
      </div>
    );
  }

  const isTicketActive = ticket.status === 'active';
  const isTicketUsed = ticket.status === 'used';
  const isTicketRevoked = ticket.status === 'revoked';

  const getStatusStyle = (status) => {
    switch (status) {
      case 'active':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'used':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      case 'revoked':
        return 'bg-red-50 text-red-700 border-red-200';
      default:
        return 'bg-slate-50 text-slate-600 border-slate-200';
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'active':
        return 'Access Permitted';
      case 'used':
        return 'Checked In';
      case 'revoked':
        return 'Ticket Revoked';
      default:
        return status.toUpperCase();
    }
  };

  const qrCodeUrl = qrToken
    ? `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent(qrToken)}`
    : '';

  return (
    <div className="p-6 md:p-8 max-w-xl mx-auto space-y-6 flex flex-col items-center">
      
      {/* Back button */}
      <div className="w-full text-left">
        <Link 
          to="/portal/tickets"
          className="inline-flex items-center space-x-2 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to My Tickets</span>
        </Link>
      </div>

      {/* Premium Event Pass Card */}
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm overflow-hidden border border-slate-150 flex flex-col relative">
        
        {/* Event details header stub */}
        <div className="bg-slate-900 p-6 text-white text-center">
          <h1 className="text-lg font-extrabold tracking-tight line-clamp-1">{ticket.event_name}</h1>
          <p className="text-slate-400 text-xs mt-1.5 font-medium flex items-center justify-center space-x-1">
            <MapPin className="h-3.5 w-3.5 text-slate-500" />
            <span>{ticket.venue}</span>
          </p>
        </div>

        {/* Side notch stub punch-outs with dashed line */}
        <div className="relative h-6 bg-white flex items-center justify-between pointer-events-none">
          <div className="absolute -left-3 h-6 w-6 rounded-full bg-slate-50 border-r border-slate-150"></div>
          <div className="w-full border-t border-dashed border-slate-200 mx-5"></div>
          <div className="absolute -right-3 h-6 w-6 rounded-full bg-slate-50 border-l border-slate-150"></div>
        </div>

        {/* Bottom card content */}
        <div className="p-6 flex flex-col items-center bg-white">
          
          {/* Status badge */}
          <span className={`px-3.5 py-1 border rounded-full text-xs font-bold uppercase tracking-wider mb-5 ${getStatusStyle(ticket.status)}`}>
            {getStatusLabel(ticket.status)}
          </span>

          {/* QR Viewport / Check in state */}
          {isTicketActive ? (
            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-150 shadow-inner flex flex-col items-center mb-6 relative group w-full max-w-[240px]">
              {qrCodeUrl ? (
                <img
                  src={qrCodeUrl}
                  alt="Secure Pass check-in code"
                  className="w-44 h-44 object-contain"
                />
              ) : (
                <div className="w-44 h-44 flex items-center justify-center text-xs text-slate-400 animate-pulse">
                  Generating secure code...
                </div>
              )}
              
              {/* Countdown indicator */}
              <div className="flex flex-col items-center mt-3 space-y-1">
                <span className="text-[10px] font-bold text-slate-450 uppercase tracking-wider">
                  Security code refreshes in {countdown}s
                </span>
                <div className="flex items-center space-x-1 text-[8px] text-slate-400 font-semibold">
                  <QrCode className="h-3 w-3" />
                  <span>Rotating ticket verification system active</span>
                </div>
              </div>
            </div>
          ) : isTicketUsed ? (
            <div className="bg-emerald-50 border border-emerald-100 p-6 rounded-2xl flex flex-col items-center text-center space-y-3 mb-6 w-full max-w-[240px]">
              <div className="p-2.5 bg-emerald-100 text-emerald-600 rounded-full border border-emerald-200">
                <CheckCircle className="h-8 w-8" />
              </div>
              <div>
                <h4 className="text-xs font-black text-emerald-800 uppercase tracking-widest">✓ CHECKED IN</h4>
                <p className="text-[10px] text-emerald-600 mt-1 max-w-[150px] mx-auto font-bold leading-normal">
                  You have already entered this event.
                </p>
              </div>
            </div>
          ) : (
            <div className="bg-slate-50 w-48 h-48 rounded-2xl border border-slate-150 flex flex-col items-center justify-center mb-6 text-center p-4">
              <XCircle className="h-10 w-10 text-red-500 mb-2 animate-pulse" />
              <p className="text-xs font-bold text-slate-800 uppercase tracking-tight">Pass Code Disabled</p>
              <p className="text-[10px] text-slate-450 mt-1 max-w-[130px] font-medium leading-relaxed">
                This barcode cannot be scanned at entrance gates.
              </p>
            </div>
          )}

          {qrError && (
            <div className="bg-red-50 text-red-700 p-2.5 rounded-lg border border-red-200 text-[10px] font-semibold text-center mb-4 max-w-[240px]">
              {qrError}
            </div>
          )}

          {/* Ticket metadata info list */}
          <div className="w-full space-y-3.5 border-t border-slate-100 pt-5 text-xs text-slate-500 font-semibold">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Attendee:</span>
              <span className="font-bold text-slate-800">{ticket.participant_name}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Ticket Code:</span>
              <span className="font-mono text-xs font-bold bg-indigo-50 border border-indigo-100 text-indigo-700 px-2 py-0.5 rounded select-all tracking-wider">
                {ticket.ticket_code}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Date:</span>
              <span className="text-slate-800">{ticket.date}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Time Bounds:</span>
              <span className="text-slate-800">{ticket.time}</span>
            </div>
            <div className="flex justify-between items-center border-t border-slate-100 pt-3">
              <span className="text-slate-400">Expires At:</span>
              <span className="text-slate-700 font-mono text-[10px]">
                {new Date(ticket.expires_at).toLocaleString()}
              </span>
            </div>
            {isTicketUsed && ticket.scanned_at && (
              <div className="flex justify-between items-center border-t border-slate-100 pt-3">
                <span className="text-emerald-600 font-bold">Checked In:</span>
                <span className="text-emerald-700 font-mono text-[10px] font-bold">
                  {new Date(ticket.scanned_at).toLocaleString()}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
      
      <span className="text-[10px] font-bold text-slate-400 tracking-widest uppercase mt-4 select-none">
        SECURE PASS ROTATING CHALLENGE NODE
      </span>
    </div>
  );
}
