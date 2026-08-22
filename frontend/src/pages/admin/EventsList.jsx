import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import {
  Calendar,
  Plus,
  Search,
  Filter,
  ArrowUpDown,
  Building,
  Users,
  MapPin,
  Clock,
  Globe,
  X,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Lock
} from 'lucide-react';

export default function EventsList() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [error, setError] = useState('');

  // Search & Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('date_desc');

  // Form Fields
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [venue, setVenue] = useState('');
  const [date, setDate] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [capacity, setCapacity] = useState(100);
  const [timezone, setTimezone] = useState('Asia/Karachi');

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/events?page_size=100');
      setEvents(res.data.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  const handleCreateEvent = async (e) => {
    e.preventDefault();
    setError('');
    
    // Quick validation before submitting
    if (capacity <= 0) {
      setError('capacity: Capacity must be greater than zero.');
      return;
    }

    try {
      await api.post('/api/events', {
        name,
        description: description || null,
        venue,
        date,
        start_time: startTime ? startTime.substring(0, 5) : '',
        end_time: endTime ? endTime.substring(0, 5) : '',
        capacity: Number(capacity),
        timezone,
      });
      setShowModal(false);
      fetchEvents();
      // Clear form
      setName('');
      setDescription('');
      setVenue('');
      setDate('');
      setStartTime('');
      setEndTime('');
      setCapacity(100);
      setTimezone('Asia/Karachi');
    } catch (err) {
      const errData = err.response?.data?.error;
      if (errData?.details) {
        const detailedMsg = Object.entries(errData.details)
          .map(([field, msg]) => `${field}: ${msg}`)
          .join(', ');
        setError(detailedMsg);
      } else {
        setError(errData?.message || 'Failed to create event.');
      }
    }
  };

  // Local Filter & Sort Logic
  const filteredEvents = events.filter(e => {
    const matchesSearch = 
      e.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
      e.venue.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesStatus = 
      statusFilter === 'all' || 
      e.status === statusFilter;
      
    return matchesSearch && matchesStatus;
  }).sort((a, b) => {
    if (sortBy === 'date_asc') return new Date(a.date) - new Date(b.date);
    if (sortBy === 'date_desc') return new Date(b.date) - new Date(a.date);
    if (sortBy === 'name_asc') return a.name.localeCompare(b.name);
    if (sortBy === 'name_desc') return b.name.localeCompare(a.name);
    return 0;
  });

  return (
    <div className="p-6 md:p-8 max-w-6xl mx-auto space-y-6">
      
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">Events</h1>
          <p className="text-slate-500 text-sm mt-0.5 font-medium">
            Manage events, registrations, capabilities and check-in options.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center space-x-2 px-4 py-2.5 bg-indigo-650 hover:bg-indigo-750 text-white rounded-lg text-sm font-bold transition-all shadow-sm shadow-indigo-600/10 cursor-pointer"
        >
          <Plus className="h-4 w-4" />
          <span>Create Event</span>
        </button>
      </div>

      {/* Filters toolbar */}
      <div className="flex flex-col md:flex-row gap-4 items-center justify-between bg-white p-4 rounded-xl border border-slate-150 shadow-xs">
        {/* Search */}
        <div className="relative w-full md:max-w-xs">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search events by name or venue..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-slate-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-lg text-sm focus:outline-none transition-all placeholder-slate-400 bg-slate-50/50"
          />
        </div>

        {/* Drodowns */}
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          {/* Status filter */}
          <div className="flex items-center space-x-2 text-xs font-semibold text-slate-550 w-full sm:w-auto">
            <Filter className="h-3.5 w-3.5 text-slate-450" />
            <span>Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-2.5 py-1.5 border border-slate-200 bg-slate-50 rounded-lg focus:outline-none text-xs font-bold text-slate-700 cursor-pointer"
            >
              <option value="all">All Statuses</option>
              <option value="draft">Draft</option>
              <option value="active">Active</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>

          {/* Sort */}
          <div className="flex items-center space-x-2 text-xs font-semibold text-slate-550 w-full sm:w-auto">
            <ArrowUpDown className="h-3.5 w-3.5 text-slate-450" />
            <span>Sort:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-2.5 py-1.5 border border-slate-200 bg-slate-50 rounded-lg focus:outline-none text-xs font-bold text-slate-700 cursor-pointer"
            >
              <option value="date_desc">Date (Newest First)</option>
              <option value="date_asc">Date (Oldest First)</option>
              <option value="name_asc">Name (A-Z)</option>
              <option value="name_desc">Name (Z-A)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Events Presentation (Table / Skeletons) */}
      {loading ? (
        <div className="bg-white rounded-xl border border-slate-150 overflow-hidden shadow-xs divide-y divide-slate-100 animate-pulse">
          {[1, 2, 3].map(i => (
            <div key={i} className="p-6 flex justify-between items-center">
              <div className="space-y-2 w-1/3">
                <div className="h-4.5 bg-slate-200 rounded w-5/6"></div>
                <div className="h-3 bg-slate-200 rounded w-1/2"></div>
              </div>
              <div className="h-4 bg-slate-200 rounded w-16"></div>
              <div className="h-4 bg-slate-200 rounded w-24"></div>
              <div className="h-8 bg-slate-200 rounded w-24"></div>
            </div>
          ))}
        </div>
      ) : filteredEvents.length === 0 ? (
        <div className="text-center py-16 bg-white border border-slate-150 rounded-xl shadow-xs flex flex-col items-center justify-center p-6">
          <div className="p-3 bg-slate-50 rounded-full text-slate-400 mb-3.5">
            <Calendar className="h-8 w-8" />
          </div>
          <h3 className="text-sm font-bold text-slate-900 tracking-tight">No Events Found</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm">
            {searchQuery || statusFilter !== 'all' 
              ? "No events match your current search queries or filters. Try adjusting them."
              : "Start by creating your first event. This will initialize access policies and check-in configurations."}
          </p>
          {!searchQuery && statusFilter === 'all' && (
            <button
              onClick={() => setShowModal(true)}
              className="mt-4 px-4 py-2 bg-indigo-600 hover:bg-indigo-755 text-white text-xs font-semibold rounded-lg shadow-sm transition-all cursor-pointer"
            >
              Create Event
            </button>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-150 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm text-slate-550">
              <thead className="bg-slate-50 text-[10px] text-slate-450 font-bold uppercase tracking-wider border-b border-slate-150">
                <tr>
                  <th className="px-6 py-4">Event</th>
                  <th className="px-6 py-4">Date</th>
                  <th className="px-6 py-4">Venue</th>
                  <th className="px-6 py-4">Capacity</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium text-slate-800">
                {filteredEvents.map((e) => (
                  <tr key={e.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-semibold text-slate-900 line-clamp-1">{e.name}</div>
                      {e.description && (
                        <div className="text-xs text-slate-400 font-normal line-clamp-1 mt-0.5">{e.description}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 text-xs font-mono">{e.date}</td>
                    <td className="px-6 py-4 text-xs">{e.venue}</td>
                    <td className="px-6 py-4 text-xs">{e.capacity} attendees</td>
                    <td className="px-6 py-4">
                      <span className={`inline-block text-[10px] px-2.5 py-0.5 border rounded-full font-bold uppercase ${
                        e.status === 'active' ? 'bg-green-50 text-green-700 border-green-200' :
                        e.status === 'completed' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                        e.status === 'cancelled' ? 'bg-red-50 text-red-700 border-red-200' :
                        'bg-slate-50 text-slate-600 border-slate-200'
                      }`}>
                        {e.status === 'active' ? 'published' : e.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link 
                        to={`/admin/events/${e.id}`}
                        className="inline-flex items-center space-x-1 px-3 py-1.5 bg-slate-50 hover:bg-indigo-50 border border-slate-200 hover:border-indigo-200 rounded-lg text-xs font-bold text-slate-700 hover:text-indigo-650 transition-all cursor-pointer"
                      >
                        <span>Manage</span>
                        <span>&rarr;</span>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Creation Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-950/60 z-50 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="bg-white rounded-xl w-full max-w-lg shadow-2xl border border-slate-150 overflow-hidden flex flex-col max-h-[90vh]">
            {/* Header */}
            <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
              <h3 className="text-base font-bold text-slate-900 tracking-tight">Create New Event</h3>
              <button 
                onClick={() => { setShowModal(false); setError(''); }}
                className="p-1 rounded-lg hover:bg-slate-50 text-slate-400 hover:text-slate-600 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Error alerts */}
            {error && (
              <div className="px-6 pt-4">
                <div className="bg-red-50/70 border border-red-200 text-red-650 text-xs p-3.5 rounded-lg flex items-start space-x-2 font-medium">
                  <AlertTriangle className="h-4.5 w-4.5 text-red-500 shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="font-bold text-red-800">Invalid Input Fields</p>
                    <p className="mt-0.5">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleCreateEvent} className="p-6 space-y-5 overflow-y-auto flex-1">
              
              {/* Event Information Section */}
              <div className="space-y-3">
                <div className="flex items-center space-x-2 text-xs font-bold text-slate-450 uppercase tracking-wider border-b border-slate-100 pb-1.5">
                  <FileText className="h-3.5 w-3.5 text-slate-400" />
                  <span>Event Information</span>
                </div>
                <div className="grid grid-cols-1 gap-3.5">
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 mb-1">Event Name</label>
                    <input
                      type="text"
                      required
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="w-full px-3 py-1.5 border border-slate-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-lg text-sm focus:outline-none bg-slate-50/30 transition-all placeholder-slate-400"
                      placeholder="e.g. Annual Tech Summit 2026"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 mb-1">Venue Location</label>
                    <input
                      type="text"
                      required
                      value={venue}
                      onChange={(e) => setVenue(e.target.value)}
                      className="w-full px-3 py-1.5 border border-slate-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-lg text-sm focus:outline-none bg-slate-50/30 transition-all placeholder-slate-400"
                      placeholder="e.g. Main Convention Center, Hall B"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 mb-1">Description (Optional)</label>
                    <textarea
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="w-full px-3 py-1.5 border border-slate-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-lg text-sm focus:outline-none bg-slate-50/30 transition-all placeholder-slate-400 h-20 resize-none"
                      placeholder="e.g. Provide details about the event topic, speakers..."
                    ></textarea>
                  </div>
                </div>
              </div>

              {/* Schedule Section */}
              <div className="space-y-3 pt-2">
                <div className="flex items-center space-x-2 text-xs font-bold text-slate-450 uppercase tracking-wider border-b border-slate-100 pb-1.5">
                  <Clock className="h-3.5 w-3.5 text-slate-400" />
                  <span>Schedule & Timezone</span>
                </div>
                <div className="grid grid-cols-2 gap-3.5">
                  <div className="col-span-2 sm:col-span-1">
                    <label className="block text-xs font-semibold text-slate-500 mb-1">Date</label>
                    <input
                      type="date"
                      required
                      value={date}
                      onChange={(e) => setDate(e.target.value)}
                      className="w-full px-3 py-1.5 border border-slate-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-lg text-sm focus:outline-none bg-slate-50/30 transition-all text-slate-700"
                    />
                  </div>
                  <div className="col-span-2 sm:col-span-1">
                    <label className="block text-xs font-semibold text-slate-500 mb-1">Timezone (IANA)</label>
                    <input
                      type="text"
                      required
                      value={timezone}
                      onChange={(e) => setTimezone(e.target.value)}
                      className="w-full px-3 py-1.5 border border-slate-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-lg text-sm focus:outline-none bg-slate-50/30 transition-all placeholder-slate-400 text-slate-700"
                      placeholder="e.g. Asia/Karachi or UTC"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 mb-1">Start Time</label>
                    <input
                      type="time"
                      required
                      value={startTime}
                      onChange={(e) => setStartTime(e.target.value)}
                      className="w-full px-3 py-1.5 border border-slate-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-lg text-sm focus:outline-none bg-slate-50/30 transition-all text-slate-700"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 mb-1">End Time</label>
                    <input
                      type="time"
                      required
                      value={endTime}
                      onChange={(e) => setEndTime(e.target.value)}
                      className="w-full px-3 py-1.5 border border-slate-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-lg text-sm focus:outline-none bg-slate-50/30 transition-all text-slate-700"
                    />
                  </div>
                </div>
              </div>

              {/* Seating / Capacity Section */}
              <div className="space-y-3 pt-2">
                <div className="flex items-center space-x-2 text-xs font-bold text-slate-450 uppercase tracking-wider border-b border-slate-100 pb-1.5">
                  <Users className="h-3.5 w-3.5 text-slate-400" />
                  <span>Capacity Limits</span>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1">Maximum Seating Capacity</label>
                  <input
                    type="number"
                    required
                    min="1"
                    value={capacity}
                    onChange={(e) => setCapacity(e.target.value)}
                    className="w-full px-3 py-1.5 border border-slate-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-lg text-sm focus:outline-none bg-slate-50/30 transition-all text-slate-700"
                    placeholder="e.g. 500"
                  />
                  <p className="text-[10px] text-slate-450 mt-1 font-medium">Specify the maximum limit of registered attendees.</p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end space-x-3 pt-5 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => { setShowModal(false); setError(''); }}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-bold transition-all cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-650 hover:bg-indigo-755 text-white rounded-lg text-xs font-bold transition-all shadow-sm cursor-pointer"
                >
                  Create Event
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
