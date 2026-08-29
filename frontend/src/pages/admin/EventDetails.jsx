import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import api from '../../services/api';
import {
  ArrowLeft,
  Calendar,
  MapPin,
  Clock,
  Users,
  CheckCircle,
  FileText,
  UploadCloud,
  FileSpreadsheet,
  Download,
  AlertTriangle,
  UserPlus,
  RefreshCw,
  Ticket,
  X,
  Trash2,
  Lock,
  ExternalLink,
  ShieldCheck,
  Search
} from 'lucide-react';

export default function EventDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [event, setEvent] = useState(null);
  const [eventStats, setEventStats] = useState(null);
  const [activeTab, setActiveTab] = useState('participants'); // 'participants' | 'tickets'
  const [loading, setLoading] = useState(true);
  const [toastMessage, setToastMessage] = useState(null);
  const [error, setError] = useState(null);

  // Participant Management states
  const [participants, setParticipants] = useState([]);
  const [partTotal, setPartTotal] = useState(0);
  const [partPage, setPartPage] = useState(1);
  const [partSearch, setPartSearch] = useState('');
  const [showAddPartModal, setShowAddPartModal] = useState(false);
  const [partName, setPartName] = useState('');
  const [partEmail, setPartEmail] = useState('');
  const [partPhone, setPartPhone] = useState('');
  const [partError, setPartError] = useState('');

  // CSV Import states
  const [showCSVModal, setShowCSVModal] = useState(false);
  const [csvFile, setCsvFile] = useState(null);
  const [csvLoading, setCsvLoading] = useState(false);
  const [csvResult, setCsvResult] = useState(null); // { success: bool, imported: int, errors: array }
  const [csvError, setCsvError] = useState('');

  // Ticket Management states
  const [tickets, setTickets] = useState([]);
  const [ticketTotal, setTicketTotal] = useState(0);
  const [ticketPage, setTicketPage] = useState(1);
  const [ticketSearch, setTicketSearch] = useState('');
  const [ticketStatus, setTicketStatus] = useState('');
  const [genLoading, setGenLoading] = useState(false);
  const [genResult, setGenResult] = useState(null);

  // Status transitions states
  const [transitionLoading, setTransitionLoading] = useState(false);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  // Fetch Event details
  const fetchEvent = async () => {
    const res = await api.get(`/api/events/${id}`);
    setEvent(res.data.data);
  };

  // Fetch Event insights/metrics
  const fetchEventStats = async () => {
    const res = await api.get(`/api/reports/event/${id}`);
    setEventStats(res.data.data);
  };

  // Fetch Participants
  const fetchParticipants = async () => {
    let url = `/api/events/${id}/participants?page=${partPage}&page_size=10`;
    if (partSearch) url += `&search=${encodeURIComponent(partSearch)}`;
    const res = await api.get(url);
    setParticipants(res.data.data);
    setPartTotal(res.data.total);
  };

  // Fetch Tickets
  const fetchTickets = async () => {
    let url = `/api/events/${id}/tickets?page=${ticketPage}&page_size=10`;
    if (ticketSearch) url += `&search=${encodeURIComponent(ticketSearch)}`;
    if (ticketStatus) url += `&status=${ticketStatus}`;
    const res = await api.get(url);
    setTickets(res.data.data);
    setTicketTotal(res.data.total);
  };

  const initData = async () => {
    setLoading(true);
    setError(null);
    try {
      await Promise.all([
        fetchEvent(),
        fetchEventStats().catch(err => {
          console.error("Non-critical Stats failure:", err);
        }),
        fetchParticipants(),
        fetchTickets()
      ]);
    } catch (err) {
      console.error("Critical details loading failure:", err);
      const errMsg = err.response?.data?.error?.message 
        || (err.response?.status ? `HTTP ${err.response.status}: ${err.message}` : err.message)
        || 'Failed to load event details.';
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    initData();
  }, [id]);

  useEffect(() => {
    const load = async () => {
      try {
        await fetchParticipants();
      } catch (err) {
        console.error("Failed to load participants on change:", err);
      }
    };
    if (event) {
      load();
    }
  }, [partPage, partSearch]);

  useEffect(() => {
    const load = async () => {
      try {
        await fetchTickets();
      } catch (err) {
        console.error("Failed to load tickets on change:", err);
      }
    };
    if (event) {
      load();
    }
  }, [ticketPage, ticketSearch, ticketStatus]);

  // Transition status of event
  const updateEventStatus = async (newStatus) => {
    if (!window.confirm(`Are you sure you want to transition event to ${newStatus}?`)) return;
    setTransitionLoading(true);
    try {
      await api.put(`/api/events/${id}`, { status: newStatus });
      await Promise.all([fetchEvent(), fetchEventStats()]);
      showToast(`Event status updated to ${newStatus}.`);
    } catch (err) {
      alert(err.response?.data?.error?.message || 'Failed to update status.');
    } finally {
      setTransitionLoading(false);
    }
  };

  const handleAddParticipant = async (e) => {
    e.preventDefault();
    setPartError('');
    try {
      await api.post(`/api/events/${id}/participants`, {
        name: partName,
        email: partEmail,
        phone: partPhone || null,
      });
      setShowAddPartModal(false);
      await Promise.all([fetchParticipants(), fetchEvent(), fetchEventStats()]);
      setPartName('');
      setPartEmail('');
      setPartPhone('');
      showToast('Participant registered successfully.');
    } catch (err) {
      setPartError(err.response?.data?.error?.message || 'Failed to register participant.');
    }
  };

  const handleDeactivateParticipant = async (partId) => {
    if (!window.confirm('Are you sure you want to deactivate this participant? This soft-delete disables their ticket.')) return;
    try {
      await api.delete(`/api/participants/${partId}`);
      await Promise.all([fetchParticipants(), fetchTickets(), fetchEvent(), fetchEventStats()]);
      showToast('Participant deactivated.');
    } catch (err) {
      alert(err.response?.data?.error?.message || 'Failed to deactivate.');
    }
  };

  // CSV Import handler
  const handleCSVUpload = async (e) => {
    e.preventDefault();
    setCsvError('');
    setCsvResult(null);

    if (!csvFile) {
      setCsvError('Please select a CSV file.');
      return;
    }

    if (csvFile.size > 2 * 1024 * 1024) {
      setCsvError('File exceeds the 2 MB limit.');
      return;
    }

    const formData = new FormData();
    formData.append('file', csvFile);

    setCsvLoading(true);
    try {
      const res = await api.post(`/api/events/${id}/participants/bulk`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setCsvResult({ success: true, imported: res.data.data.imported });
      setCsvFile(null);
      await Promise.all([fetchParticipants(), fetchEvent(), fetchEventStats(), fetchTickets()]);
      showToast(`${res.data.data.imported} participants imported bulk.`);
    } catch (err) {
      const errResponse = err.response?.data?.error;
      setCsvResult({
        success: false,
        errors: errResponse?.details?.errors || [{ message: errResponse?.message || 'Upload failed.' }]
      });
    } finally {
      setCsvLoading(false);
    }
  };

  // Generate Tickets
  const handleGenerateTickets = async () => {
    setGenLoading(true);
    setGenResult(null);
    try {
      const res = await api.post(`/api/events/${id}/tickets/generate`);
      setGenResult(`Generated ${res.data.data.generated} new tickets.`);
      await Promise.all([fetchTickets(), fetchEventStats()]);
      showToast('Tickets generated successfully.');
    } catch (err) {
      alert(err.response?.data?.error?.message || 'Failed to generate.');
    } finally {
      setGenLoading(false);
    }
  };

  // Revoke Ticket
  const handleRevokeTicket = async (ticketId) => {
    if (!window.confirm('Are you sure you want to revoke this ticket? This action cannot be undone.')) return;
    try {
      await api.post(`/api/tickets/${ticketId}/revoke`);
      await Promise.all([fetchTickets(), fetchEventStats()]);
      showToast('Ticket code revoked.');
    } catch (err) {
      alert(err.response?.data?.error?.message || 'Failed to revoke.');
    }
  };

  // Export CSV
  const handleExportCSV = () => {
    const url = `${api.defaults.baseURL || ''}/api/reports/event/${id}/export`;
    window.open(url, '_blank');
  };

  if (error) {
    return (
      <div className="p-8 max-w-lg mx-auto space-y-6 text-center">
        <div className="bg-red-50 border border-red-200 text-red-700 p-6 rounded-xl space-y-2">
          <h3 className="font-extrabold text-base">Unable to Load Event Details</h3>
          <p className="text-xs font-semibold opacity-90">{error}</p>
        </div>
        <div className="flex justify-center space-x-3">
          <button
            onClick={initData}
            className="inline-flex items-center space-x-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-755 text-white rounded-lg text-xs font-bold transition-all shadow-xs cursor-pointer"
          >
            <span>Retry</span>
          </button>
          <Link
            to="/admin/events"
            className="inline-flex items-center space-x-1.5 px-4 py-2 bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 rounded-lg text-xs font-bold transition-all shadow-2xs"
          >
            <span>Back to Events</span>
          </Link>
        </div>
      </div>
    );
  }

  if (loading || !event) {
    return (
      <div className="p-8 max-w-6xl mx-auto space-y-6 animate-pulse">
        <div className="h-6 bg-slate-200 rounded w-1/6"></div>
        <div className="h-10 bg-slate-200 rounded w-1/3"></div>
        <div className="h-32 bg-slate-200 rounded-xl"></div>
        <div className="h-96 bg-slate-200 rounded-xl"></div>
      </div>
    );
  }

  const partTotalPages = Math.ceil(partTotal / 10);
  const ticketTotalPages = Math.ceil(ticketTotal / 10);

  return (
    <div className="p-6 md:p-8 max-w-6xl mx-auto space-y-8">
      {/* Toast Alert */}
      {toastMessage && (
        <div className="fixed bottom-4 right-4 bg-slate-900 border border-slate-800 text-slate-100 px-4 py-3 rounded-lg shadow-xl text-xs flex items-center space-x-2 animate-bounce z-50">
          <CheckCircle className="h-4 w-4 text-emerald-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Back Link */}
      <div>
        <Link 
          to="/admin/events"
          className="inline-flex items-center space-x-2 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Events</span>
        </Link>
      </div>

      {/* Event Header Card */}
      <div className="bg-white rounded-xl border border-slate-150 shadow-xs p-6 relative overflow-hidden">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 pb-6 border-b border-slate-100">
          <div>
            <div className="flex items-center space-x-2">
              <span className={`text-[10px] px-2.5 py-0.5 border rounded-full font-bold uppercase tracking-wider ${
                event.status === 'active' ? 'bg-green-50 text-green-700 border-green-200' :
                event.status === 'completed' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                event.status === 'cancelled' ? 'bg-red-50 text-red-700 border-red-200' :
                'bg-slate-50 text-slate-650 border-slate-200'
              }`}>
                {event.status === 'active' ? 'published' : event.status}
              </span>
              <span className="text-xs text-slate-400 font-medium">Event Control Panel</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 mt-2.5 tracking-tight">{event.name}</h1>
            {event.description && (
              <p className="text-slate-500 text-sm mt-1.5 max-w-2xl font-medium">{event.description}</p>
            )}
          </div>

          {/* Core Controls */}
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            {event.status === 'draft' && (
              <>
                <button 
                  onClick={() => updateEventStatus('active')} 
                  disabled={transitionLoading}
                  className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold transition-all shadow-xs cursor-pointer disabled:opacity-50"
                >
                  Publish Event
                </button>
                <button 
                  onClick={() => updateEventStatus('cancelled')}
                  disabled={transitionLoading}
                  className="px-3.5 py-2 bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 rounded-lg text-xs font-bold transition-all cursor-pointer disabled:opacity-50"
                >
                  Cancel Event
                </button>
              </>
            )}
            {event.status === 'active' && (
              <>
                <button 
                  onClick={() => updateEventStatus('completed')}
                  disabled={transitionLoading}
                  className="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-755 text-white rounded-lg text-xs font-bold transition-all shadow-xs cursor-pointer disabled:opacity-50"
                >
                  Complete Event
                </button>
                <button 
                  onClick={() => updateEventStatus('cancelled')}
                  disabled={transitionLoading}
                  className="px-3.5 py-2 bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 rounded-lg text-xs font-bold transition-all cursor-pointer disabled:opacity-50"
                >
                  Cancel Event
                </button>
              </>
            )}
            <button
              onClick={handleExportCSV}
              className="flex items-center space-x-1.5 px-3.5 py-2 bg-white hover:bg-slate-50 text-slate-700 hover:text-slate-900 border border-slate-200 rounded-lg text-xs font-bold transition-all shadow-xs cursor-pointer"
            >
              <Download className="h-3.5 w-3.5" />
              <span>Export CSV</span>
            </button>
          </div>
        </div>

        {/* Info Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 pt-6 text-xs text-slate-500 font-semibold">
          <div className="space-y-1">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Venue</span>
            <div className="flex items-center space-x-1.5 text-slate-800">
              <MapPin className="h-4 w-4 text-slate-450 shrink-0" />
              <span className="truncate">{event.venue}</span>
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Date</span>
            <div className="flex items-center space-x-1.5 text-slate-800">
              <Calendar className="h-4 w-4 text-slate-450 shrink-0" />
              <span>{event.date}</span>
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Time Bounds</span>
            <div className="flex items-center space-x-1.5 text-slate-800">
              <Clock className="h-4 w-4 text-slate-450 shrink-0" />
              <span>{event.start_time} - {event.end_time} ({event.timezone})</span>
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Capacity</span>
            <div className="flex items-center space-x-1.5 text-slate-800">
              <Users className="h-4 w-4 text-slate-450 shrink-0" />
              <span>{event.capacity} total capacity</span>
            </div>
          </div>
        </div>
      </div>

      {/* KPI Stats Overview Cards */}
      {eventStats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
          <div className="bg-white p-5 rounded-xl border border-slate-150 shadow-xs">
            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Total Registered</span>
            <p className="text-2xl font-extrabold text-slate-900 mt-1">{eventStats.tickets_issued}</p>
          </div>
          <div className="bg-white p-5 rounded-xl border border-slate-150 shadow-xs">
            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Checked In</span>
            <p className="text-2xl font-extrabold text-emerald-650 mt-1">{eventStats.checked_in}</p>
          </div>
          <div className="bg-white p-5 rounded-xl border border-slate-150 shadow-xs">
            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Remaining seats</span>
            <p className="text-2xl font-extrabold text-slate-900 mt-1">{eventStats.remaining}</p>
          </div>
          <div className="bg-white p-5 rounded-xl border border-slate-150 shadow-xs">
            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Attendance Rate</span>
            <p className="text-2xl font-extrabold text-indigo-650 mt-1">{eventStats.attendance_percentage}%</p>
          </div>
        </div>
      )}

      {/* Tab Selectors */}
      <div className="flex border-b border-slate-200">
        <button
          onClick={() => setActiveTab('participants')}
          className={`px-6 py-3 border-b-2 font-bold text-sm transition-all cursor-pointer ${
            activeTab === 'participants' 
              ? 'border-indigo-650 text-indigo-650' 
              : 'border-transparent text-slate-400 hover:text-slate-700'
          }`}
        >
          Participants
        </button>
        <button
          onClick={() => setActiveTab('tickets')}
          className={`px-6 py-3 border-b-2 font-bold text-sm transition-all cursor-pointer ${
            activeTab === 'tickets' 
              ? 'border-indigo-650 text-indigo-650' 
              : 'border-transparent text-slate-400 hover:text-slate-700'
          }`}
        >
          Tickets Allocated
        </button>
      </div>

      {/* Tab Content: Participants */}
      {activeTab === 'participants' && (
        <div className="bg-white rounded-xl border border-slate-150 shadow-xs p-6 space-y-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            {/* Search */}
            <div className="relative w-full sm:max-w-xs">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search by name or email..."
                value={partSearch}
                onChange={(e) => { setPartSearch(e.target.value); setPartPage(1); }}
                className="w-full pl-9 pr-4 py-2 border border-slate-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-lg text-sm focus:outline-none transition-all placeholder-slate-400 bg-slate-50/50"
              />
            </div>

            {/* Actions */}
            <div className="flex items-center space-x-2 w-full sm:w-auto shrink-0">
              <button
                onClick={() => setShowCSVModal(true)}
                disabled={event.status !== 'active'}
                className="flex items-center space-x-2 px-3.5 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-750 border border-indigo-200 rounded-lg text-xs font-bold transition-all disabled:opacity-50 cursor-pointer"
              >
                <UploadCloud className="h-4 w-4" />
                <span>Bulk Import CSV</span>
              </button>
              <button
                onClick={() => setShowAddPartModal(true)}
                disabled={event.status !== 'active'}
                className="flex items-center space-x-2 px-3.5 py-2 bg-slate-900 hover:bg-slate-950 text-white rounded-lg text-xs font-bold transition-all disabled:opacity-50 cursor-pointer"
              >
                <UserPlus className="h-4 w-4" />
                <span>Add Participant</span>
              </button>
            </div>
          </div>

          {participants.length === 0 ? (
            <div className="text-center py-12 bg-slate-50/50 border border-dashed border-slate-200 rounded-xl p-6">
              <Users className="h-7 w-7 text-slate-400 mx-auto mb-2" />
              <p className="text-sm font-semibold text-slate-800">No Participants Registered</p>
              <p className="text-xs text-slate-500 mt-1">Register attendees manually or upload a CSV configuration.</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="overflow-x-auto border border-slate-150 rounded-lg">
                <table className="min-w-full text-left text-sm text-slate-550">
                  <thead className="bg-slate-50 text-[10px] text-slate-450 font-bold uppercase tracking-wider border-b border-slate-150">
                    <tr>
                      <th className="px-6 py-3">Name</th>
                      <th className="px-6 py-3">Email Address</th>
                      <th className="px-6 py-3">Phone</th>
                      <th className="px-6 py-3">Status</th>
                      <th className="px-6 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-medium text-slate-800">
                    {participants.map((p) => (
                      <tr key={p.id} className="hover:bg-slate-50/30 transition-colors">
                        <td className="px-6 py-4 font-semibold text-slate-900">{p.name}</td>
                        <td className="px-6 py-4 text-xs font-mono">{p.email}</td>
                        <td className="px-6 py-4 text-xs">{p.phone || '-'}</td>
                        <td className="px-6 py-4">
                          <span className={`inline-block text-[10px] px-2 py-0.5 border rounded-full font-bold uppercase ${
                            p.is_active ? 'bg-green-50 text-green-700 border-green-200' : 'bg-red-50 text-red-700 border-red-200'
                          }`}>
                            {p.is_active ? 'Active' : 'Deactivated'}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right">
                          {p.is_active && (
                            <button
                              onClick={() => handleDeactivateParticipant(p.id)}
                              className="inline-flex items-center space-x-1 px-2.5 py-1.5 bg-white hover:bg-red-50 text-slate-700 hover:text-red-650 border border-slate-200 hover:border-red-200 rounded-lg text-xs font-bold transition-all cursor-pointer"
                            >
                              <Trash2 className="h-3.5 w-3.5 shrink-0" />
                              <span>Deactivate</span>
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {partTotalPages > 1 && (
                <div className="flex items-center justify-between text-xs font-semibold text-slate-550 pt-2">
                  <span>Page {partPage} of {partTotalPages}</span>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setPartPage(p => Math.max(p - 1, 1))}
                      disabled={partPage === 1}
                      className="px-3 py-1.5 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-700 font-bold transition-colors disabled:opacity-50 cursor-pointer"
                    >
                      Prev
                    </button>
                    <button
                      onClick={() => setPartPage(p => Math.min(p + 1, partTotalPages))}
                      disabled={partPage === partTotalPages}
                      className="px-3 py-1.5 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-700 font-bold transition-colors disabled:opacity-50 cursor-pointer"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Tab Content: Tickets */}
      {activeTab === 'tickets' && (
        <div className="bg-white rounded-xl border border-slate-150 shadow-xs p-6 space-y-6">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            {/* Left elements: Search + Filter status */}
            <div className="flex flex-col sm:flex-row gap-3 w-full sm:max-w-md">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search by ticket code..."
                  value={ticketSearch}
                  onChange={(e) => { setTicketSearch(e.target.value); setTicketPage(1); }}
                  className="w-full pl-9 pr-4 py-2 border border-slate-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-lg text-sm focus:outline-none transition-all placeholder-slate-400 bg-slate-50/50"
                />
              </div>

              <select
                value={ticketStatus}
                onChange={(e) => { setTicketStatus(e.target.value); setTicketPage(1); }}
                className="px-3 py-2 border border-slate-200 bg-slate-50 rounded-lg focus:outline-none text-xs font-bold text-slate-700 cursor-pointer"
              >
                <option value="">All Ticket Statuses</option>
                <option value="active">Active</option>
                <option value="checked_in">Checked In</option>
                <option value="revoked">Revoked</option>
              </select>
            </div>

            {/* Right actions: Generate tickets */}
            <div className="flex items-center space-x-2 shrink-0 w-full md:w-auto">
              <button
                onClick={handleGenerateTickets}
                disabled={genLoading || event.status !== 'active'}
                className="flex items-center justify-center space-x-2 w-full md:w-auto px-4 py-2 bg-indigo-650 hover:bg-indigo-755 text-white rounded-lg text-xs font-bold transition-all disabled:opacity-50 cursor-pointer shadow-xs"
              >
                {genLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Ticket className="h-4 w-4" />}
                <span>Generate Tickets</span>
              </button>
            </div>
          </div>

          {/* Ticket generation feedback banner */}
          {genResult && (
            <div className="bg-emerald-50 border border-emerald-200 text-emerald-700 px-4 py-3 rounded-lg text-xs font-semibold flex items-center space-x-2">
              <CheckCircle className="h-4.5 w-4.5 text-emerald-500" />
              <span>{genResult}</span>
            </div>
          )}

          {tickets.length === 0 ? (
            <div className="text-center py-12 bg-slate-50/50 border border-dashed border-slate-200 rounded-xl p-6">
              <Ticket className="h-7 w-7 text-slate-400 mx-auto mb-2" />
              <p className="text-sm font-semibold text-slate-800">No Tickets Allocated</p>
              <p className="text-xs text-slate-500 mt-1">Tickets are generated based on registered participants list.</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="overflow-x-auto border border-slate-150 rounded-lg">
                <table className="min-w-full text-left text-sm text-slate-550">
                  <thead className="bg-slate-50 text-[10px] text-slate-450 font-bold uppercase tracking-wider border-b border-slate-150">
                    <tr>
                      <th className="px-6 py-3">Ticket Code</th>
                      <th className="px-6 py-3">Expires At</th>
                      <th className="px-6 py-3">Status</th>
                      <th className="px-6 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-medium text-slate-800">
                    {tickets.map((t) => (
                      <tr key={t.id} className="hover:bg-slate-50/30 transition-colors">
                        <td className="px-6 py-4">
                          <span className="font-mono text-xs bg-slate-100 text-slate-800 px-2.5 py-1 rounded-md border border-slate-150 font-bold select-all tracking-wider">
                            {t.ticket_code}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-xs font-mono">{t.expires_at}</td>
                        <td className="px-6 py-4">
                          <span className={`inline-block text-[10px] px-2.5 py-0.5 border rounded-full font-bold uppercase ${
                            t.status === 'active' ? 'bg-green-50 text-green-700 border-green-200' :
                            t.status === 'checked_in' ? 'bg-indigo-50 text-indigo-700 border-indigo-200' :
                            'bg-red-50 text-red-705 border-red-200'
                          }`}>
                            {t.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right">
                          {t.status === 'active' && (
                            <button
                              onClick={() => handleRevokeTicket(t.id)}
                              className="inline-flex items-center space-x-1 px-2.5 py-1.5 bg-white hover:bg-red-50 text-slate-700 hover:text-red-650 border border-slate-200 hover:border-red-200 rounded-lg text-xs font-bold transition-all cursor-pointer"
                            >
                              <Lock className="h-3.5 w-3.5 shrink-0" />
                              <span>Revoke</span>
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {ticketTotalPages > 1 && (
                <div className="flex items-center justify-between text-xs font-semibold text-slate-550 pt-2">
                  <span>Page {ticketPage} of {ticketTotalPages}</span>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setTicketPage(t => Math.max(t - 1, 1))}
                      disabled={ticketPage === 1}
                      className="px-3 py-1.5 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-700 font-bold transition-colors disabled:opacity-50 cursor-pointer"
                    >
                      Prev
                    </button>
                    <button
                      onClick={() => setTicketPage(t => Math.min(t + 1, ticketTotalPages))}
                      disabled={ticketPage === ticketTotalPages}
                      className="px-3 py-1.5 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-700 font-bold transition-colors disabled:opacity-50 cursor-pointer"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Modal: Add Participant */}
      {showAddPartModal && (
        <div className="fixed inset-0 bg-slate-950/60 z-50 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="bg-white rounded-xl w-full max-w-md shadow-2xl border border-slate-150 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
              <h3 className="text-base font-bold text-slate-900 tracking-tight font-sans">Add Participant</h3>
              <button 
                onClick={() => { setShowAddPartModal(false); setPartError(''); }}
                className="p-1 rounded-lg hover:bg-slate-50 text-slate-400 hover:text-slate-600 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {partError && (
              <div className="px-6 pt-4">
                <div className="bg-red-50 text-red-650 text-xs p-3 rounded-lg flex items-center space-x-2 font-medium">
                  <AlertTriangle className="h-4 w-4 shrink-0" />
                  <span>{partError}</span>
                </div>
              </div>
            )}

            <form onSubmit={handleAddParticipant} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={partName}
                  onChange={(e) => setPartName(e.target.value)}
                  className="w-full px-3 py-1.5 border border-slate-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-lg text-sm focus:outline-none bg-slate-50/30"
                  placeholder="e.g. John Doe"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1">Email Address</label>
                <input
                  type="email"
                  required
                  value={partEmail}
                  onChange={(e) => setPartEmail(e.target.value)}
                  className="w-full px-3 py-1.5 border border-slate-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-lg text-sm focus:outline-none bg-slate-50/30"
                  placeholder="e.g. john@example.com"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1">Phone Number (Optional)</label>
                <input
                  type="text"
                  value={partPhone}
                  onChange={(e) => setPartPhone(e.target.value)}
                  className="w-full px-3 py-1.5 border border-slate-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-lg text-sm focus:outline-none bg-slate-50/30"
                  placeholder="e.g. +123456789"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => { setShowAddPartModal(false); setPartError(''); }}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-bold transition-all cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-650 hover:bg-indigo-755 text-white rounded-lg text-xs font-bold transition-all cursor-pointer"
                >
                  Register
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: CSV Upload */}
      {showCSVModal && (
        <div className="fixed inset-0 bg-slate-950/60 z-50 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="bg-white rounded-xl w-full max-w-md shadow-2xl border border-slate-150 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
              <h3 className="text-base font-bold text-slate-900 tracking-tight">Bulk Import CSV</h3>
              <button 
                onClick={() => { setShowCSVModal(false); setCsvError(''); setCsvResult(null); }}
                className="p-1 rounded-lg hover:bg-slate-50 text-slate-400 hover:text-slate-600 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleCSVUpload} className="p-6 space-y-5">
              {/* Drag Drop Area Container */}
              <div className="border-2 border-dashed border-slate-200 hover:border-indigo-400 bg-slate-50 hover:bg-slate-100/50 rounded-xl p-6 transition-all text-center flex flex-col items-center justify-center cursor-pointer relative group">
                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => setCsvFile(e.target.files[0])}
                  className="absolute inset-0 opacity-0 cursor-pointer z-10"
                />
                <FileSpreadsheet className="h-9 w-9 text-slate-400 group-hover:text-indigo-500 transition-colors mb-2.5" />
                <span className="text-xs font-bold text-slate-800">
                  {csvFile ? csvFile.name : 'Click to select or drag CSV file'}
                </span>
                <span className="text-[10px] text-slate-450 mt-1 font-semibold block">Maximum limit 2 MB (.csv format)</span>
              </div>

              {/* Error messages inside modal */}
              {csvError && (
                <div className="bg-red-50 text-red-650 text-xs p-3 rounded-lg flex items-center space-x-2 font-medium">
                  <AlertTriangle className="h-4 w-4 shrink-0" />
                  <span>{csvError}</span>
                </div>
              )}

              {/* Bulk results panel */}
              {csvResult && (
                <div className={`p-4 rounded-lg text-xs font-medium border ${
                  csvResult.success 
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-750' 
                    : 'bg-red-50 border-red-200 text-red-750'
                }`}>
                  {csvResult.success ? (
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="h-4.5 w-4.5 text-emerald-500" />
                      <span>Successfully imported {csvResult.imported} participants.</span>
                    </div>
                  ) : (
                    <div className="space-y-1.5">
                      <p className="font-bold flex items-center space-x-2 text-red-800">
                        <AlertTriangle className="h-4.5 w-4.5 text-red-500" />
                        <span>Failed to import CSV lines:</span>
                      </p>
                      <ul className="list-disc list-inside pl-1 space-y-1 text-[11px] overflow-y-auto max-h-24">
                        {csvResult.errors.map((e, index) => (
                          <li key={index} className="truncate">{e.message || 'Row parsing error.'}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              <div className="flex justify-end space-x-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => { setShowCSVModal(false); setCsvError(''); setCsvResult(null); }}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-bold transition-all cursor-pointer"
                >
                  Close
                </button>
                <button
                  type="submit"
                  disabled={csvLoading}
                  className="flex items-center space-x-2 px-4 py-2 bg-indigo-650 hover:bg-indigo-755 text-white rounded-lg text-xs font-bold transition-all disabled:opacity-50 cursor-pointer shadow-xs"
                >
                  {csvLoading && <RefreshCw className="h-3.5 w-3.5 animate-spin" />}
                  <span>Upload CSV</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
