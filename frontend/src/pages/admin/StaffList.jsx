import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import {
  Users,
  UserPlus,
  Mail,
  Lock,
  Eye,
  EyeOff,
  CheckCircle2,
  AlertTriangle,
  X,
  User,
  ShieldCheck,
  RefreshCw,
  Power
} from 'lucide-react';

export default function StaffList() {
  const [staffList, setStaffList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [error, setError] = useState('');
  const [toastMessage, setToastMessage] = useState(null);

  // Form Fields
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const fetchStaff = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/users/staff');
      setStaffList(res.data.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStaff();
  }, []);

  const handleCreateStaff = async (e) => {
    e.preventDefault();
    setError('');

    if (password.length < 6) {
      setError('password: Password must contain at least 6 characters.');
      return;
    }

    try {
      await api.post('/api/users/staff', {
        name,
        email,
        password
      });
      setShowModal(false);
      fetchStaff();
      setName('');
      setEmail('');
      setPassword('');
      setShowPassword(false);
      showToast('Staff member added successfully.');
    } catch (err) {
      const errData = err.response?.data?.error;
      if (errData?.details) {
        const detailedMsg = Object.entries(errData.details)
          .map(([field, msg]) => `${field}: ${msg}`)
          .join(', ');
        setError(detailedMsg);
      } else {
        setError(errData?.message || 'Failed to create staff account.');
      }
    }
  };

  const toggleStaffStatus = async (staffId, currentStatus) => {
    const actionText = currentStatus ? 'deactivate' : 'reactivate';
    if (!window.confirm(`Are you sure you want to ${actionText} this staff member?`)) return;
    try {
      await api.put(`/api/users/staff/${staffId}`, { is_active: !currentStatus });
      fetchStaff();
      showToast(`Staff member ${currentStatus ? 'deactivated' : 'activated'}.`);
    } catch (err) {
      alert(err.response?.data?.error?.message || 'Failed to update status.');
    }
  };

  const getInitials = (name) => {
    return name
      ? name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2)
      : 'U';
  };

  return (
    <div className="p-6 md:p-8 max-w-6xl mx-auto space-y-6">
      {/* Toast alert */}
      {toastMessage && (
        <div className="fixed bottom-4 right-4 bg-slate-900 border border-slate-800 text-slate-100 px-4 py-3 rounded-lg shadow-xl text-xs flex items-center space-x-2 animate-bounce z-50">
          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Title Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">Staff Scanners</h1>
          <p className="text-slate-500 text-sm mt-0.5 font-medium">
            Manage the credentials and statuses of staff members authorized to operate gate scanners.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center space-x-2 px-4 py-2.5 bg-indigo-655 hover:bg-indigo-755 text-white rounded-lg text-sm font-bold transition-all shadow-sm shadow-indigo-600/10 cursor-pointer"
        >
          <UserPlus className="h-4 w-4" />
          <span>Add Staff Member</span>
        </button>
      </div>

      {/* Staff Table */}
      {loading ? (
        <div className="bg-white rounded-xl border border-slate-150 overflow-hidden shadow-xs divide-y divide-slate-100 animate-pulse">
          {[1, 2, 3].map(i => (
            <div key={i} className="p-6 flex justify-between items-center">
              <div className="space-y-2 w-1/4">
                <div className="h-4.5 bg-slate-200 rounded w-5/6"></div>
                <div className="h-3 bg-slate-200 rounded w-1/2"></div>
              </div>
              <div className="h-4 bg-slate-200 rounded w-24"></div>
              <div className="h-4 bg-slate-200 rounded w-16"></div>
              <div className="h-8 bg-slate-200 rounded w-24"></div>
            </div>
          ))}
        </div>
      ) : staffList.length === 0 ? (
        <div className="text-center py-16 bg-white border border-slate-150 rounded-xl shadow-xs flex flex-col items-center justify-center p-6">
          <div className="p-3 bg-slate-50 rounded-full text-slate-400 mb-3.5">
            <Users className="h-8 w-8" />
          </div>
          <h3 className="text-sm font-bold text-slate-900 tracking-tight">No Staff Accounts Created</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm">
            Add staff members to grant them scanner privileges for verifying tickets at the gates.
          </p>
          <button
            onClick={() => setShowModal(true)}
            className="mt-4 px-4 py-2 bg-indigo-650 hover:bg-indigo-755 text-white text-xs font-semibold rounded-lg shadow-sm transition-all cursor-pointer"
          >
            Add Staff Member
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-150 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm text-slate-555">
              <thead className="bg-slate-50 text-[10px] text-slate-450 font-bold uppercase tracking-wider border-b border-slate-150">
                <tr>
                  <th className="px-6 py-4">Staff Member</th>
                  <th className="px-6 py-4">Email Address</th>
                  <th className="px-6 py-4">Role</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium text-slate-800">
                {staffList.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-3">
                        <div className="h-8 w-8 rounded-lg bg-indigo-50 border border-indigo-100/50 text-indigo-750 flex items-center justify-center font-bold text-xs">
                          {getInitials(s.name)}
                        </div>
                        <span className="font-semibold text-slate-900">{s.name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-xs font-mono">{s.email}</td>
                    <td className="px-6 py-4 text-xs">
                      <span className="inline-flex items-center space-x-1 uppercase tracking-wider text-[10px] bg-slate-100 text-slate-700 px-2.5 py-0.5 rounded font-bold border border-slate-200">
                        {s.role}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-block text-[10px] px-2.5 py-0.5 border rounded-full font-bold uppercase ${
                        s.is_active ? 'bg-green-50 text-green-700 border-green-200' : 'bg-red-50 text-red-700 border-red-200'
                      }`}>
                        {s.is_active ? 'Active' : 'Deactivated'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => toggleStaffStatus(s.id, s.is_active)}
                        className={`inline-flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-xs font-bold border transition-all cursor-pointer ${
                          s.is_active 
                            ? 'bg-white hover:bg-red-50 border-slate-200 hover:border-red-200 text-slate-700 hover:text-red-650' 
                            : 'bg-white hover:bg-green-50 border-slate-200 hover:border-green-200 text-slate-700 hover:text-green-650'
                        }`}
                      >
                        <Power className="h-3.5 w-3.5" />
                        <span>{s.is_active ? 'Deactivate' : 'Activate'}</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Add Staff Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-950/60 z-50 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="bg-white rounded-xl w-full max-w-md shadow-2xl border border-slate-150 overflow-hidden">
            {/* Header */}
            <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
              <h3 className="text-base font-bold text-slate-900 tracking-tight">Add Staff Member</h3>
              <button 
                onClick={() => { setShowModal(false); setError(''); }}
                className="p-1 rounded-lg hover:bg-slate-50 text-slate-400 hover:text-slate-650 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Validation alerts */}
            {error && (
              <div className="px-6 pt-4">
                <div className="bg-red-50 text-red-650 text-xs p-3 rounded-lg flex items-center space-x-2 font-medium">
                  <AlertTriangle className="h-4 w-4 shrink-0" />
                  <span>{error}</span>
                </div>
              </div>
            )}

            <form onSubmit={handleCreateStaff} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1">Full Name</label>
                <div className="relative">
                  <User className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full pl-9 pr-4 py-1.5 border border-slate-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-lg text-sm focus:outline-none bg-slate-50/30"
                    placeholder="e.g. John Doe"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-9 pr-4 py-1.5 border border-slate-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-lg text-sm focus:outline-none bg-slate-50/30"
                    placeholder="e.g. staff@securegate.com"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-9 pr-10 py-1.5 border border-slate-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-lg text-sm focus:outline-none bg-slate-50/30"
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-2 text-slate-400 hover:text-slate-600 focus:outline-none"
                  >
                    {showPassword ? <EyeOff className="h-4.5 w-4.5" /> : <Eye className="h-4.5 w-4.5" />}
                  </button>
                </div>
                <p className="text-[10px] text-slate-400 mt-1 font-medium">Must be at least 6 characters long.</p>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => { setShowModal(false); setError(''); }}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-bold transition-all cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-650 hover:bg-indigo-755 text-white rounded-lg text-xs font-bold transition-all cursor-pointer"
                >
                  Create Account
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
