import React, { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// Eagerly load critical public entry pages
import Login from '../pages/auth/Login';
import Register from '../pages/auth/Register';
import PublicTicket from '../pages/public/PublicTicket';

// Lazy load role-specific and heavy scanner modules for code splitting
const Scanner = lazy(() => import('../pages/staff/Scanner'));
const History = lazy(() => import('../pages/staff/History'));
const Dashboard = lazy(() => import('../pages/admin/Dashboard'));
const EventsList = lazy(() => import('../pages/admin/EventsList'));
const EventDetails = lazy(() => import('../pages/admin/EventDetails'));
const StaffList = lazy(() => import('../pages/admin/StaffList'));
const AuditLogs = lazy(() => import('../pages/admin/AuditLogs'));

// Lazy load Attendee Portal pages
const PortalDashboard = lazy(() => import('../pages/portal/Dashboard'));
const PortalAvailableEvents = lazy(() => import('../pages/portal/AvailableEvents'));
const PortalAvailableEventDetails = lazy(() => import('../pages/portal/AvailableEventDetails'));
const PortalEvents = lazy(() => import('../pages/portal/Events'));
const PortalEventDetails = lazy(() => import('../pages/portal/EventDetails'));
const PortalTickets = lazy(() => import('../pages/portal/Tickets'));
const PortalTicketDetails = lazy(() => import('../pages/portal/TicketDetails'));
const PortalProfile = lazy(() => import('../pages/portal/Profile'));

const PageLoader = () => (
  <div className="flex items-center justify-center p-12 text-xs font-bold text-slate-400 uppercase tracking-widest animate-pulse">
    Loading interface...
  </div>
);

function ProtectedRoute({ children, requiredRole }) {
  const { user } = useAuth();
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (requiredRole === 'admin' && user.role !== 'admin') {
    if (user.role === 'attendee') return <Navigate to="/portal" replace />;
    return <Navigate to="/staff/scanner" replace />;
  }
  if (requiredRole === 'staff' && user.role !== 'staff' && user.role !== 'admin') {
    if (user.role === 'attendee') return <Navigate to="/portal" replace />;
    return <Navigate to="/login" replace />;
  }
  if (requiredRole === 'attendee' && user.role !== 'attendee') {
    if (user.role === 'admin') return <Navigate to="/admin/dashboard" replace />;
    if (user.role === 'staff') return <Navigate to="/staff/scanner" replace />;
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default function AppRoutes() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/tickets/:token" element={<PublicTicket />} />

        {/* Staff Protected routes */}
        <Route
          path="/staff/scanner"
          element={
            <ProtectedRoute requiredRole="staff">
              <Scanner />
            </ProtectedRoute>
          }
        />
        <Route
          path="/staff/history"
          element={
            <ProtectedRoute requiredRole="staff">
              <History />
            </ProtectedRoute>
          }
        />

        {/* Admin Protected routes */}
        <Route
          path="/admin/dashboard"
          element={
            <ProtectedRoute requiredRole="admin">
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/events"
          element={
            <ProtectedRoute requiredRole="admin">
              <EventsList />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/events/:id"
          element={
            <ProtectedRoute requiredRole="admin">
              <EventDetails />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/staff"
          element={
            <ProtectedRoute requiredRole="admin">
              <StaffList />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/audit-logs"
          element={
            <ProtectedRoute requiredRole="admin">
              <AuditLogs />
            </ProtectedRoute>
          }
        />

        {/* Attendee Portal Protected routes */}
        <Route
          path="/portal"
          element={
            <ProtectedRoute requiredRole="attendee">
              <PortalDashboard />
            </ProtectedRoute>
          }
        />
        {/* Static routes must be declared before dynamic parameters */}
        <Route
          path="/portal/events/available"
          element={
            <ProtectedRoute requiredRole="attendee">
              <PortalAvailableEvents />
            </ProtectedRoute>
          }
        />
        <Route
          path="/portal/events/available/:id"
          element={
            <ProtectedRoute requiredRole="attendee">
              <PortalAvailableEventDetails />
            </ProtectedRoute>
          }
        />
        <Route
          path="/portal/events"
          element={
            <ProtectedRoute requiredRole="attendee">
              <PortalEvents />
            </ProtectedRoute>
          }
        />
        <Route
          path="/portal/events/:id"
          element={
            <ProtectedRoute requiredRole="attendee">
              <PortalEventDetails />
            </ProtectedRoute>
          }
        />
        <Route
          path="/portal/tickets"
          element={
            <ProtectedRoute requiredRole="attendee">
              <PortalTickets />
            </ProtectedRoute>
          }
        />
        <Route
          path="/portal/tickets/:id"
          element={
            <ProtectedRoute requiredRole="attendee">
              <PortalTicketDetails />
            </ProtectedRoute>
          }
        />
        <Route
          path="/portal/profile"
          element={
            <ProtectedRoute requiredRole="attendee">
              <PortalProfile />
            </ProtectedRoute>
          }
        />

        {/* Fallback route */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </Suspense>
  );
}
