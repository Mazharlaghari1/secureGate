import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import {
  User,
  Mail,
  ShieldCheck,
  RefreshCw,
  AlertTriangle,
  CheckCircle2
} from 'lucide-react';

export default function PortalProfile() {
  const { user, setUser } = useAuth();
  const [name, setName] = useState(user?.name || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [toastMessage, setToastMessage] = useState(null);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await api.put('/api/portal/profile', { name });
      setUser(res.data.data);
      showToast('Profile updated successfully.');
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to update profile.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 md:p-8 max-w-xl mx-auto space-y-6">
      
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-4 right-4 bg-slate-900 border border-slate-800 text-slate-100 px-4 py-3 rounded-lg shadow-xl text-xs flex items-center space-x-2 animate-bounce z-50">
          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">Your Profile</h1>
        <p className="text-slate-500 text-sm mt-0.5 font-medium">
          Manage your personal details and account settings.
        </p>
      </div>

      {/* Form Card */}
      <div className="bg-white rounded-xl border border-slate-150 shadow-xs p-6">
        {error && (
          <div className="mb-4 bg-red-50 text-red-700 text-xs p-3 rounded-lg flex items-center space-x-2 font-medium">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleUpdateProfile} className="space-y-5">
          {/* Full Name */}
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1.5">Full Name</label>
            <div className="relative">
              <User className="absolute left-3.5 top-3 h-4 w-4 text-slate-450" />
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-slate-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-xl text-sm focus:outline-none bg-slate-50/20 transition-all font-medium text-slate-800"
                placeholder="e.g. John Doe"
              />
            </div>
          </div>

          {/* Email Address (Read-only) */}
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1.5">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
              <input
                type="email"
                disabled
                value={user?.email || ''}
                className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-xl text-sm bg-slate-50 text-slate-400 font-medium cursor-not-allowed"
              />
            </div>
            <p className="text-[10px] text-slate-400 mt-1 font-semibold">Your email is managed by your registration and cannot be modified.</p>
          </div>

          {/* Account Status (Display) */}
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1.5">Account Security Status</label>
            <div className="flex items-center space-x-2.5 bg-slate-50 p-4 rounded-xl border border-slate-150">
              <div className="p-1.5 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-100">
                <ShieldCheck className="h-4.5 w-4.5" />
              </div>
              <div className="text-xs">
                <p className="text-slate-800 font-bold">Attendee Profile Verified</p>
                <p className="text-slate-450 mt-0.5 font-medium">Your credentials are cryptographically protected via SecureGate tokens.</p>
              </div>
            </div>
          </div>

          {/* Update button */}
          <div className="border-t border-slate-100 pt-5 flex justify-end">
            <button
              type="submit"
              disabled={loading}
              className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-755 text-white rounded-lg text-xs font-bold transition-all shadow-xs cursor-pointer disabled:opacity-50"
            >
              {loading && <RefreshCw className="h-3.5 w-3.5 animate-spin" />}
              <span>Save Profile Changes</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
