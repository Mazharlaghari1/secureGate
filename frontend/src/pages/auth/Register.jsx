import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../../services/api';
import { 
  ShieldCheck, 
  Mail, 
  Lock, 
  User,
  Eye, 
  EyeOff, 
  AlertTriangle,
  RefreshCw,
  Fingerprint
} from 'lucide-react';

export default function Register() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      await api.post('/api/auth/register', {
        name,
        email,
        password
      });
      setSuccess('Account created successfully! Redirecting to login page...');
      setTimeout(() => {
        navigate('/login');
      }, 2500);
    } catch (err) {
      const errResponse = err.response?.data?.error;
      if (errResponse?.details) {
        const detailedMsg = Object.entries(errResponse.details)
          .map(([field, msg]) => `${field}: ${msg}`)
          .join(', ');
        setError(detailedMsg);
      } else {
        setError(errResponse?.message || 'Registration failed.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col md:flex-row">
      
      {/* Left Column: SaaS Branding */}
      <div className="hidden md:flex md:w-1/2 bg-slate-900 border-r border-slate-850 p-12 flex-col justify-between relative overflow-hidden">
        <div className="absolute inset-0 opacity-5 pointer-events-none">
          <div className="absolute inset-0" style={{
            backgroundImage: 'radial-gradient(circle, #4F46E5 1px, transparent 1px)',
            backgroundSize: '24px 24px'
          }}></div>
        </div>

        <div className="flex items-center space-x-2.5 relative z-10">
          <div className="p-2 rounded-xl bg-indigo-600/10 border border-indigo-500/20">
            <ShieldCheck className="h-6 w-6 text-indigo-500" />
          </div>
          <span className="font-extrabold text-xl tracking-tight text-white">SecureGate</span>
        </div>

        <div className="max-w-md space-y-6 relative z-10">
          <h2 className="text-3xl lg:text-4xl font-extrabold text-white tracking-tight leading-tight">
            Claim your digital pass in seconds.
          </h2>
          <p className="text-slate-400 text-sm leading-relaxed font-medium">
            Create an attendee account to instantly access your registered events, verify your check-in statuses, and display secure cryptographic tickets at the gate.
          </p>

          <div className="flex items-center space-x-3.5 bg-slate-950/40 p-4 rounded-xl border border-slate-800 backdrop-blur-md">
            <div className="h-8 w-8 rounded-lg bg-indigo-650 flex items-center justify-center text-white shrink-0 shadow-inner">
              <Fingerprint className="h-4.5 w-4.5" />
            </div>
            <div className="text-xs">
              <p className="text-slate-200 font-bold">Attendee Registration</p>
              <p className="text-slate-450 mt-0.5 font-medium">Login credentials tied to your ticket enrollment email.</p>
            </div>
          </div>
        </div>

        <div className="text-xs font-semibold text-slate-500 relative z-10">
          &copy; {new Date().getFullYear()} SecureGate Access Systems. All rights reserved.
        </div>
      </div>

      {/* Right Column: Registration Form */}
      <div className="flex-1 flex flex-col justify-center items-center px-6 py-12 md:p-16 relative">
        <div className="md:hidden flex items-center space-x-2.5 mb-8">
          <ShieldCheck className="h-7 w-7 text-indigo-500" />
          <span className="font-extrabold text-xl tracking-tight text-white">SecureGate</span>
        </div>

        <div className="w-full max-w-sm space-y-6 bg-slate-900 border border-slate-850 p-8 rounded-2xl shadow-2xl relative z-10 text-white">
          <div>
            <h2 className="text-xl md:text-2xl font-bold tracking-tight">Create your account</h2>
            <p className="text-xs text-slate-400 mt-1.5 font-medium">Get started as an attendee to access your tickets</p>
          </div>

          {/* Success Banner */}
          {success && (
            <div className="bg-emerald-950/20 border border-emerald-900/50 text-emerald-400 text-xs p-3.5 rounded-xl flex items-start space-x-2 font-medium">
              <ShieldCheck className="h-4.5 w-4.5 text-emerald-500 shrink-0 mt-0.5" />
              <span>{success}</span>
            </div>
          )}

          {/* Error Banner */}
          {error && (
            <div className="bg-red-950/20 border border-red-900/50 text-red-400 text-xs p-3.5 rounded-xl flex items-start space-x-2 font-medium">
              <AlertTriangle className="h-4.5 w-4.5 text-red-500 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Full Name */}
            <div className="space-y-1">
              <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">Full Name</label>
              <div className="relative">
                <User className="absolute left-3.5 top-3 h-4 w-4 text-slate-500" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="w-full pl-10 pr-4 py-2 bg-slate-950 border border-slate-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-xl text-sm focus:outline-none transition-all placeholder-slate-505 text-slate-100"
                  placeholder="e.g. John Doe"
                />
              </div>
            </div>

            {/* Email Field */}
            <div className="space-y-1">
              <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-3 h-4 w-4 text-slate-500" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full pl-10 pr-4 py-2 bg-slate-950 border border-slate-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-xl text-sm focus:outline-none transition-all placeholder-slate-505 text-slate-100"
                  placeholder="john@example.com"
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="space-y-1">
              <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3 h-4 w-4 text-slate-500" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full pl-10 pr-10 py-2 bg-slate-950 border border-slate-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-xl text-sm focus:outline-none transition-all placeholder-slate-505 text-slate-100"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-2.5 text-slate-500 hover:text-slate-350 focus:outline-none cursor-pointer"
                >
                  {showPassword ? <EyeOff className="h-4.5 w-4.5" /> : <Eye className="h-4.5 w-4.5" />}
                </button>
              </div>
            </div>

            {/* Action button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-2.5 bg-indigo-600 hover:bg-indigo-755 text-white rounded-xl text-sm font-bold transition-all shadow-md shadow-indigo-600/10 cursor-pointer disabled:opacity-50 flex items-center justify-center space-x-2"
            >
              {loading && <RefreshCw className="h-4 w-4 animate-spin shrink-0" />}
              <span>Sign Up</span>
            </button>
          </form>

          <div className="text-center pt-2">
            <p className="text-xs text-slate-400">
              Already have an account?{' '}
              <Link to="/login" className="text-indigo-400 hover:text-indigo-350 font-bold transition-colors">
                Sign In
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
