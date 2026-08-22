import React, { useEffect, useRef, useState } from 'react';
import { Html5Qrcode } from 'html5-qrcode';
import api from '../../services/api';
import {
  Scan,
  RefreshCw,
  Camera,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Clock,
  User,
  ArrowRight
} from 'lucide-react';

export default function Scanner() {
  const [events, setEvents] = useState([]);
  const [selectedEventId, setSelectedEventId] = useState('');
  const [cameraActive, setCameraActive] = useState(false);
  const [scanResult, setScanResult] = useState(null); // { success: bool, code: string, message: string, data: object }
  const [loading, setLoading] = useState(false);
  const [cameraError, setCameraError] = useState('');
  const [recentScans, setRecentScans] = useState([]); // List of recent scans in this session

  const qrCodeRegionId = 'qr-reader-viewport';
  const html5QrCodeRef = useRef(null);
  const lastScannedTokenRef = useRef('');
  const isProcessingRef = useRef(false);
  const detectStartRef = useRef(null);

  // Fetch events on mount
  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const res = await api.get('/api/events?page_size=100');
        const activeEvents = res.data.data.filter(e => e.status === 'active');
        setEvents(activeEvents);
        if (activeEvents.length > 0) {
          setSelectedEventId(activeEvents[0].id);
        }
      } catch (err) {
        console.error('Failed to load events:', err);
      }
    };
    fetchEvents();
  }, []);

  // Cleanup scanner on unmount
  useEffect(() => {
    return () => {
      stopScanner();
    };
  }, []);

  const startScanner = async () => {
    if (!selectedEventId) return;
    setCameraError('');
    setScanResult(null);
    lastScannedTokenRef.current = '';
    isProcessingRef.current = false;

    const start_time = performance.now();
    try {
      const html5QrCode = new Html5Qrcode(qrCodeRegionId);
      html5QrCodeRef.current = html5QrCode;

      await html5QrCode.start(
        { facingMode: 'environment' },
        {
          fps: 15,
          qrbox: { width: 250, height: 250 },
        },
        onScanSuccess,
        onScanFailure
      );
      const end_time = performance.now();
      console.log(`[Scanner Diagnostics] Camera initialized in ${(end_time - start_time).toFixed(2)}ms`);
      setCameraActive(true);
    } catch (err) {
      console.error('Camera initialization failed:', err);
      setCameraError('Camera access denied. Please grant permission in browser settings.');
      setCameraActive(false);
    }
  };

  const stopScanner = async () => {
    if (html5QrCodeRef.current && html5QrCodeRef.current.isScanning) {
      try {
        await html5QrCodeRef.current.stop();
        html5QrCodeRef.current = null;
      } catch (err) {
        console.error('Failed to stop camera stream:', err);
      }
    }
    setCameraActive(false);
  };

  const extractToken = (scannedText) => {
    if (!scannedText) return '';
    const text = scannedText.trim();

    // 1. Direct JWT token
    if (text.startsWith('eyJ')) {
      console.log(`[Scanner Diagnostics] Detected Raw JWT token format: ${text.substring(0, 10)}...`);
      return text;
    }

    // 2. SECUREGATE_QR:<TOKEN> format
    if (text.startsWith('SECUREGATE_QR:')) {
      const token = text.substring('SECUREGATE_QR:'.length).trim();
      if (token.startsWith('eyJ')) {
        console.log(`[Scanner Diagnostics] Detected SECUREGATE_QR prefix format: ${token.substring(0, 10)}...`);
        return token;
      }
    }

    // 3. URL format containing /tickets/
    try {
      const parts = text.split('/tickets/');
      if (parts.length === 2) {
        const token = parts[1].trim();
        if (token.startsWith('eyJ')) {
          console.log(`[Scanner Diagnostics] Detected URL format with token: ${token.substring(0, 10)}...`);
          return token;
        }
      }
    } catch (e) {
      // ignore
    }

    console.warn(`[Scanner Diagnostics] Scanned format unrecognized: "${text.substring(0, 30)}..."`);
    return '';
  };

  const onScanSuccess = async (decodedText) => {
    if (isProcessingRef.current) return;

    console.log(`[Scanner Diagnostics] QR code detected on camera viewport.`);
    const token = extractToken(decodedText);
    if (!token) {
      isProcessingRef.current = true;
      setScanResult({
        success: false,
        code: 'TICKET_INVALID',
        message: 'Invalid QR Code structure. Scanned URL is not a SecureGate pass.'
      });
      return;
    }

    if (token === lastScannedTokenRef.current) {
      console.log(`[Scanner Diagnostics] Scanned token is duplicate of last scanned token.`);
      return;
    }
    lastScannedTokenRef.current = token;
    isProcessingRef.current = true;

    console.log(`[Scanner Diagnostics] Token extraction successful (${token.substring(0, 10)}...). Verification request starting...`);
    verifyTicket(token);
  };

  const onScanFailure = (error) => {
    // Noise ignore
  };

  const verifyTicket = async (token) => {
    setLoading(true);
    const apiStart = performance.now();
    try {
      const res = await api.post('/api/attendance/verify', {
        token,
        event_id: selectedEventId
      });
      const apiEnd = performance.now();
      console.log(`[Scanner Diagnostics] Backend API verification roundtrip completed in ${(apiEnd - apiStart).toFixed(2)}ms`);
      const data = res.data.data;
      console.log(`[Scanner Diagnostics] Verification Result: APPROVED, Attendee Name: "${data.participant.name}", Ticket: "${data.ticket_code}"`);
      
      setScanResult({
        success: true,
        data
      });

      // Add to session log
      setRecentScans(prev => [
        {
          id: data.ticket_id,
          name: data.participant.name,
          code: data.ticket_code,
          time: new Date().toLocaleTimeString(),
          success: true
        },
        ...prev.slice(0, 4)
      ]);
    } catch (err) {
      const apiEnd = performance.now();
      const status = err.response?.status || 'Network Error';
      const errResponse = err.response?.data?.error;
      const failMsg = errResponse?.message || 'Verification rejected by gate policies.';
      
      console.error(`[Scanner Diagnostics] Backend API verification failed in ${(apiEnd - apiStart).toFixed(2)}ms (HTTP ${status})`);
      console.error(`[Scanner Diagnostics] Verification Result: DENIED, Code: "${errResponse?.code || 'VERIFICATION_FAILED'}", Message: "${failMsg}"`);

      setScanResult({
        success: false,
        code: errResponse?.code || 'VERIFICATION_FAILED',
        message: failMsg
      });

      setRecentScans(prev => [
        {
          id: Math.random().toString(),
          name: 'Unknown Attendee',
          code: 'REJECTED',
          time: new Date().toLocaleTimeString(),
          success: false,
          reason: failMsg
        },
        ...prev.slice(0, 4)
      ]);
    } finally {
      setLoading(false);
    }
  };

  const closeResultAndResume = () => {
    setScanResult(null);
    lastScannedTokenRef.current = '';
    isProcessingRef.current = false;
  };

  return (
    <div className="p-6 md:p-8 max-w-4xl mx-auto space-y-8 flex flex-col items-center">
      
      {/* Keyframe Scan Line Animation Style */}
      <style>{`
        @keyframes scan-animation {
          0% { top: 0%; }
          50% { top: 100%; }
          100% { top: 0%; }
        }
        .anim-scan-line {
          animation: scan-animation 2.5s infinite linear;
        }
      `}</style>

      {/* Main Container */}
      <div className="bg-white rounded-xl border border-slate-150 shadow-xs p-6 w-full max-w-xl space-y-6">
        <div>
          <h2 className="text-xl md:text-2xl font-extrabold text-slate-900 tracking-tight flex items-center justify-center space-x-2">
            <Scan className="h-6 w-6 text-indigo-600 animate-pulse" />
            <span>SecureGate Scanner</span>
          </h2>
          <p className="text-center text-xs text-slate-500 font-medium mt-1">
            Stand-by camera access-control check-in node.
          </p>
        </div>

        {/* Event Selection */}
        <div className="space-y-1.5">
          <label className="block text-xs font-bold text-slate-450 uppercase tracking-wider">
            Target Check-in Event
          </label>
          <select
            value={selectedEventId}
            onChange={(e) => {
              setSelectedEventId(e.target.value);
              stopScanner();
            }}
            disabled={cameraActive}
            className="w-full px-3 py-2 border border-slate-200 bg-slate-50 rounded-lg focus:outline-none text-xs font-bold text-slate-750 disabled:bg-slate-100 disabled:cursor-not-allowed cursor-pointer"
          >
            {events.length === 0 ? (
              <option value="">No Active Events Found</option>
            ) : (
              events.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.name} — {e.venue}
                </option>
              ))
            )}
          </select>
        </div>

        {/* Camera Viewport Area */}
        <div className="relative bg-slate-950 rounded-xl overflow-hidden aspect-square w-full max-w-md mx-auto border border-slate-800 shadow-lg flex items-center justify-center">
          <div id={qrCodeRegionId} className="w-full h-full object-cover"></div>

          {/* Scanner corner brackets */}
          {cameraActive && !scanResult && (
            <div className="absolute inset-0 p-10 pointer-events-none flex flex-col justify-between">
              <div className="flex justify-between">
                <div className="h-6 w-6 border-t-2 border-l-2 border-indigo-500 rounded-tl-sm"></div>
                <div className="h-6 w-6 border-t-2 border-r-2 border-indigo-500 rounded-tr-sm"></div>
              </div>
              <div className="flex justify-between">
                <div className="h-6 w-6 border-b-2 border-l-2 border-indigo-500 rounded-bl-sm"></div>
                <div className="h-6 w-6 border-b-2 border-r-2 border-indigo-500 rounded-br-sm"></div>
              </div>
            </div>
          )}

          {/* Scanning Animation Line */}
          {cameraActive && !scanResult && (
            <div className="absolute left-6 right-6 h-0.5 bg-indigo-500 shadow-md shadow-indigo-600/50 pointer-events-none anim-scan-line"></div>
          )}

          {/* Camera inactive state */}
          {!cameraActive && !scanResult && (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-900/90 text-white text-center p-6 space-y-4">
              <div className="p-3 bg-slate-800 rounded-xl border border-slate-700">
                <Camera className="h-7 w-7 text-slate-300" />
              </div>
              <div>
                <p className="text-sm font-bold text-slate-100">Ready to Scan</p>
                <p className="text-xs text-slate-400 max-w-xs mt-1">Select the event and launch the device camera to start access validation.</p>
              </div>
              <button
                onClick={startScanner}
                disabled={!selectedEventId}
                className="px-6 py-2 bg-indigo-600 hover:bg-indigo-755 text-white font-bold rounded-lg text-xs transition-all shadow-md shadow-indigo-600/10 cursor-pointer disabled:opacity-50"
              >
                Start Camera Node
              </button>
              {cameraError && <p className="text-red-400 text-xs mt-2">{cameraError}</p>}
            </div>
          )}

          {/* Loading server check */}
          {loading && (
            <div className="absolute inset-0 bg-slate-950/80 flex flex-col items-center justify-center text-white space-y-2.5 z-20 backdrop-blur-xs">
              <RefreshCw className="h-6 w-6 animate-spin text-indigo-500" />
              <span className="text-xs font-bold tracking-wider uppercase text-slate-300">Checking ticket validity...</span>
            </div>
          )}

          {/* Success / Failure overlay */}
          {scanResult && (
            <div
              className={`absolute inset-0 flex flex-col items-center justify-center text-center p-6 text-white z-10 transition-all ${
                scanResult.success
                  ? 'bg-emerald-650'
                  : scanResult.code === 'TICKET_ALREADY_USED'
                  ? 'bg-amber-600'
                  : 'bg-red-650'
              }`}
            >
              {scanResult.success ? (
                <div className="space-y-4">
                  <CheckCircle2 className="h-16 w-16 text-white mx-auto animate-bounce" />
                  <div>
                    <h3 className="text-xl font-extrabold tracking-tight uppercase">Access Granted</h3>
                    <p className="text-lg font-bold mt-2">{scanResult.data.participant.name}</p>
                    <p className="text-xs opacity-90 font-mono mt-1 select-all">Code: {scanResult.data.ticket_code}</p>
                    <p className="text-xs opacity-80 mt-1 font-semibold">{scanResult.data.event.name}</p>
                  </div>
                  <p className="text-[10px] opacity-60 font-mono">
                    Scanned At: {new Date(scanResult.data.scanned_at).toLocaleTimeString()}
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  <XCircle className="h-16 w-16 text-white mx-auto animate-pulse" />
                  <div>
                    <h3 className="text-xl font-extrabold tracking-tight uppercase">
                      {scanResult.code === 'TICKET_ALREADY_USED'
                        ? 'Already Checked In'
                        : scanResult.code === 'TICKET_WRONG_EVENT'
                        ? 'Wrong Event'
                        : scanResult.code === 'TICKET_EXPIRED'
                        ? 'Ticket Expired'
                        : scanResult.code === 'TICKET_REVOKED'
                        ? 'Ticket Revoked'
                        : scanResult.code === 'PARTICIPANT_INACTIVE'
                        ? 'Inactive Attendee'
                        : 'Access Denied'}
                    </h3>
                    <p className="text-xs font-semibold mt-3 opacity-90 max-w-xs mx-auto leading-relaxed">{scanResult.message}</p>
                  </div>
                </div>
              )}

              <button
                onClick={closeResultAndResume}
                className="mt-8 px-5 py-2.5 bg-white text-slate-900 hover:bg-slate-100 rounded-lg text-xs font-bold transition-all cursor-pointer shadow-md tracking-wider uppercase"
              >
                {scanResult.success ? 'Scan Next Ticket' : 'Dismiss & Scan Again'}
              </button>
            </div>
          )}
        </div>

        {cameraActive && (
          <button
            onClick={stopScanner}
            className="w-full py-2.5 bg-slate-900 hover:bg-slate-950 text-white rounded-lg text-xs font-bold transition-all shadow-xs cursor-pointer"
          >
            Shutdown Scanner
          </button>
        )}
      </div>

      {/* Recent Activity session logger */}
      <div className="w-full max-w-xl bg-white rounded-xl border border-slate-150 shadow-xs p-6">
        <h3 className="text-xs font-bold text-slate-450 uppercase tracking-wider mb-4">Gate Scanning Feed (Session)</h3>
        {recentScans.length === 0 ? (
          <p className="text-xs text-slate-450 italic text-center py-4">No tickets scanned in this session yet.</p>
        ) : (
          <div className="space-y-3">
            {recentScans.map((log) => (
              <div key={log.id} className="flex justify-between items-center text-xs font-medium border-b border-slate-50 pb-2">
                <div className="flex items-center space-x-2">
                  {log.success ? (
                    <div className="h-2 w-2 rounded-full bg-emerald-500"></div>
                  ) : (
                    <div className="h-2 w-2 rounded-full bg-red-500"></div>
                  )}
                  <span className="font-bold text-slate-800">{log.name}</span>
                  <span className="text-[10px] bg-slate-100 px-1.5 py-0.5 rounded text-slate-450 font-mono">{log.code}</span>
                </div>
                <div className="text-slate-400 font-mono text-[10px] flex items-center space-x-1.5">
                  <span>{log.time}</span>
                  {!log.success && <AlertTriangle className="h-3 w-3 text-red-500" title={log.reason} />}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
