import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  ShieldCheck, 
  LayoutDashboard, 
  Calendar, 
  Users, 
  ShieldAlert, 
  Scan, 
  History, 
  LogOut, 
  Menu, 
  X,
  User,
  Ticket,
  Home,
  Compass
} from 'lucide-react';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  if (!user) return null;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    // Admin routes
    {
      label: 'Dashboard',
      path: '/admin/dashboard',
      icon: LayoutDashboard,
      role: 'admin'
    },
    {
      label: 'Events',
      path: '/admin/events',
      icon: Calendar,
      role: 'admin'
    },
    {
      label: 'Staff',
      path: '/admin/staff',
      icon: Users,
      role: 'admin'
    },
    {
      label: 'Audit Logs',
      path: '/admin/audit-logs',
      icon: ShieldAlert,
      role: 'admin'
    },
    // Staff/Admin both routes
    {
      label: 'Scanner',
      path: '/staff/scanner',
      icon: Scan,
      role: 'both' 
    },
    {
      label: 'Scan History',
      path: '/staff/history',
      icon: History,
      role: 'both'
    },
    // Attendee routes
    {
      label: 'Home',
      path: '/portal',
      icon: Home,
      role: 'attendee',
      exact: true
    },
    {
      label: 'Browse Events',
      path: '/portal/events/available',
      icon: Compass,
      role: 'attendee'
    },
    {
      label: 'My Events',
      path: '/portal/events',
      icon: Calendar,
      role: 'attendee'
    },
    {
      label: 'My Tickets',
      path: '/portal/tickets',
      icon: Ticket,
      role: 'attendee'
    },
    {
      label: 'Profile',
      path: '/portal/profile',
      icon: User,
      role: 'attendee'
    }
  ];

  const filteredItems = navItems.filter(item => {
    if (item.role === 'admin') return user.role === 'admin';
    if (item.role === 'attendee') return user.role === 'attendee';
    if (item.role === 'both') return user.role === 'admin' || user.role === 'staff';
    return false;
  });

  const getInitials = (name) => {
    return name
      ? name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2)
      : 'U';
  };

  const isLinkActive = (item) => {
    if (item.exact) {
      return location.pathname === item.path;
    }
    return location.pathname.startsWith(item.path);
  };

  return (
    <>
      {/* Mobile Sticky Header */}
      <header className="md:hidden flex items-center justify-between px-4 py-3 bg-slate-900 border-b border-slate-800 sticky top-0 z-40 text-white">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="h-6 w-6 text-indigo-500" />
          <span className="font-bold text-base tracking-tight">SecureGate</span>
        </div>
        <button 
          onClick={() => setMobileOpen(!mobileOpen)}
          className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
        >
          {mobileOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </header>

      {/* Mobile Drawer Backdrop */}
      {mobileOpen && (
        <div 
          onClick={() => setMobileOpen(false)}
          className="md:hidden fixed inset-0 bg-slate-950/60 z-40 transition-opacity backdrop-blur-xs"
        />
      )}

      {/* Mobile Drawer Menu */}
      <div className={`md:hidden fixed top-0 bottom-0 left-0 w-72 bg-slate-900 text-white z-50 transform ${mobileOpen ? 'translate-x-0' : '-translate-x-full'} transition-transform duration-300 ease-in-out border-r border-slate-800 flex flex-col justify-between`}>
        <div className="p-5">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center space-x-2">
              <ShieldCheck className="h-6 w-6 text-indigo-500" />
              <span className="font-bold text-lg tracking-tight">SecureGate</span>
            </div>
            <button onClick={() => setMobileOpen(false)} className="text-slate-400 hover:text-white">
              <X className="h-5 w-5" />
            </button>
          </div>

          <nav className="space-y-1">
            {filteredItems.map(item => {
              const Icon = item.icon;
              const isActive = isLinkActive(item);
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileOpen(false)}
                  className={`flex items-center space-x-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                    isActive 
                      ? 'bg-indigo-600/90 text-white shadow-sm shadow-indigo-600/10' 
                      : 'text-slate-350 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  <Icon className={`h-4.5 w-4.5 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User Card at bottom of drawer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/20 flex flex-col space-y-4">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-lg bg-indigo-600 text-white flex items-center justify-center font-semibold text-sm">
              {getInitials(user.name)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-slate-200 truncate">{user.name}</p>
              <p className="text-xs text-slate-450 truncate capitalize">{user.role}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center justify-center space-x-2 w-full py-2 bg-slate-850 hover:bg-red-950/40 border border-slate-800 hover:border-red-900/50 text-slate-300 hover:text-red-400 rounded-lg text-xs font-semibold transition-all animate-none"
          >
            <LogOut className="h-3.5 w-3.5" />
            <span>Logout</span>
          </button>
        </div>
      </div>

      {/* Desktop Left Sidebar */}
      <aside className="hidden md:flex flex-col justify-between w-64 bg-slate-900 border-r border-slate-850 text-white h-screen sticky top-0 shrink-0">
        <div className="p-6">
          {/* Logo Brand */}
          <div className="flex items-center space-x-2.5 mb-8">
            <div className="p-1.5 rounded-lg bg-indigo-600/10 border border-indigo-500/20">
              <ShieldCheck className="h-6 w-6 text-indigo-500" />
            </div>
            <span className="font-extrabold text-xl tracking-tight text-slate-100">SecureGate</span>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1">
            {filteredItems.map(item => {
              const Icon = item.icon;
              const isActive = isLinkActive(item);
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                    isActive 
                      ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/20 border-l-2 border-indigo-400' 
                      : 'text-slate-350 hover:bg-slate-850 hover:text-white border-l-2 border-transparent'
                  }`}
                >
                  <Icon className={`h-4.5 w-4.5 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer User Card */}
        <div className="p-5 border-t border-slate-850 bg-slate-950/20 flex flex-col space-y-4">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-lg bg-indigo-600/90 text-white flex items-center justify-center font-semibold text-sm border border-indigo-550 shadow-inner">
              {getInitials(user.name)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-slate-100 truncate">{user.name}</p>
              <p className="text-xs text-slate-400 truncate capitalize">{user.role}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center justify-center space-x-2 w-full py-2 bg-slate-850 hover:bg-red-950/30 border border-slate-800 hover:border-red-900/30 text-slate-300 hover:text-red-400 rounded-lg text-xs font-semibold transition-all cursor-pointer"
          >
            <LogOut className="h-3.5 w-3.5" />
            <span>Logout</span>
          </button>
        </div>
      </aside>
    </>
  );
}
