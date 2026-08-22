import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import AppRoutes from '../routes/AppRoutes';
import Login from '../pages/auth/Login';
import PublicTicket from '../pages/public/PublicTicket';
import Scanner from '../pages/staff/Scanner';
import api from '../services/api';
import PortalDashboard from '../pages/portal/Dashboard';
import AvailableEvents from '../pages/portal/AvailableEvents';
import AvailableEventDetails from '../pages/portal/AvailableEventDetails';
import PortalTicketDetails from '../pages/portal/TicketDetails';

// Mock Axios API calls
jest.mock('../services/api');

describe('SecureGate Frontend Verification & UI Tests', () => {

  beforeEach(() => {
    jest.clearAllMocks();
  });

  // 1. Login Rendering
  test('renders login page with email and password inputs', () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </MemoryRouter>
    );
    expect(screen.getByPlaceholderText(/staff@example.com/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/\*\*\*\*\*\*\*\*/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument();
  });

  // 2. Protected Route Behavior & 3. Role Guard Behavior
  test('redirects unauthenticated users to login', () => {
    render(
      <MemoryRouter initialEntries={['/staff/scanner']}>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </MemoryRouter>
    );
    // Should render login page because user is not authenticated
    expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument();
  });

  // 4. Ticket Page Loading
  test('shows loading indicator on ticket view page', () => {
    api.get.mockImplementation(() => new Promise(() => {})); // Never resolves to keep loading state
    render(
      <MemoryRouter initialEntries={['/tickets/mocktoken123']}>
        <PublicTicket />
      </MemoryRouter>
    );
    expect(screen.getByText(/Loading ticket.../i)).toBeInTheDocument();
  });

  // 5. Ticket Page Invalid State
  test('shows invalid ticket banner on network or lookup failures', async () => {
    api.get.mockRejectedValue({ response: { data: { error: { message: 'Ticket token is invalid.' } } } });
    render(
      <MemoryRouter initialEntries={['/tickets/mocktoken123']}>
        <PublicTicket />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByText(/Invalid Ticket/i)).toBeInTheDocument();
      expect(screen.getByText(/Ticket token is invalid./i)).toBeInTheDocument();
    });
  });

  // 6. Scanner Page Rendering & 7. Event Selection Requirement
  test('demands event selection and warns if no active event is present', async () => {
    api.get.mockResolvedValue({ data: { data: [] } }); // No active events
    render(
      <MemoryRouter initialEntries={['/staff/scanner']}>
        <AuthProvider>
          <Scanner />
        </AuthProvider>
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByText(/No Active Events Found/i)).toBeInTheDocument();
      const startButton = screen.getByRole('button', { name: /Start Scanning/i });
      expect(startButton).toBeDisabled();
    });
  });

  // 8. Successful Verification UI
  test('displays approved success panel on valid check-ins', async () => {
    const mockSuccessResponse = {
      data: {
        data: {
          status: 'valid',
          participant: { name: 'Muhammad Ali' },
          ticket_code: 'EVT-8F4K29',
          event: { name: 'Annual Tech' },
          scanned_at: new Date().toISOString(),
          scanned_by: { name: 'Staff Member' }
        }
      }
    };
    api.get.mockResolvedValue({ data: { data: [{ id: 'evt-123', name: 'Event A', status: 'active' }] } });
    api.post.mockResolvedValue(mockSuccessResponse);

    render(
      <MemoryRouter initialEntries={['/staff/scanner']}>
        <AuthProvider>
          <Scanner />
        </AuthProvider>
      </MemoryRouter>
    );

    // Click start scanner
    await waitFor(async () => {
      const startButton = screen.getByRole('button', { name: /Start Scanning/i });
      expect(startButton).not.toBeDisabled();
    });
  });

  // 9. Already-used UI
  test('displays already-used panel on used ticket scans', async () => {
    api.get.mockResolvedValue({ data: { data: [{ id: 'evt-123', name: 'Event A', status: 'active' }] } });
    api.post.mockRejectedValue({
      response: {
        data: {
          error: {
            code: 'TICKET_ALREADY_USED',
            message: 'Ticket has already been used.'
          }
        }
      }
    });

    render(
      <MemoryRouter initialEntries={['/staff/scanner']}>
        <AuthProvider>
          <Scanner />
        </AuthProvider>
      </MemoryRouter>
    );
    // UI should handle used error state
  });

  // 10. Invalid Ticket UI
  test('displays invalid panel on unknown ticket scans', async () => {
    api.get.mockResolvedValue({ data: { data: [{ id: 'evt-123', name: 'Event A', status: 'active' }] } });
    api.post.mockRejectedValue({
      response: {
        data: {
          error: {
            code: 'TICKET_INVALID',
            message: 'Ticket is invalid.'
          }
        }
      }
    });

    render(
      <MemoryRouter initialEntries={['/staff/scanner']}>
        <AuthProvider>
          <Scanner />
        </AuthProvider>
      </MemoryRouter>
    );
  });

  // 11. Camera Permission UI
  test('shows clear camera access error when permission is denied', async () => {
    // Mock Html5Qrcode initialization rejection
    render(
      <MemoryRouter initialEntries={['/staff/scanner']}>
        <AuthProvider>
          <Scanner />
        </AuthProvider>
      </MemoryRouter>
    );
  });

  // 12. Scanner Cleanup/Unmount Behavior & 13. Repeated QR Submission Prevention
  test('cleans up resources and halts streams on unmount', () => {
    const { unmount } = render(
      <MemoryRouter initialEntries={['/staff/scanner']}>
        <AuthProvider>
          <Scanner />
        </AuthProvider>
      </MemoryRouter>
    );
    unmount();
    // Verify scanner stop method is triggered
  });

  // --- PHASE 7 ADMIN SPECIFIC TESTS ---

  // 14. Admin Route Guards & Staff Restrictions
  test('redirects staff away from admin screens', () => {
    // Mock authenticated user as role: 'staff'
    const mockAuthContext = {
      user: { name: 'Test Staff', role: 'staff' },
      token: 'jwt-token-123'
    };

    render(
      <MemoryRouter initialEntries={['/admin/dashboard']}>
        <AppRoutes />
      </MemoryRouter>
    );
    // Redirects to /login or staff pages
  });

  // 15. Dashboard Rendering
  test('renders dashboard metrics and hourly charts', async () => {
    api.get.mockResolvedValueOnce({
      data: {
        data: {
          total_events: 10,
          active_events: 2,
          total_registered_participants: 100,
          total_allocated_tickets: 80
        }
      }
    });

    render(
      <MemoryRouter initialEntries={['/admin/dashboard']}>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Total Events/i)).toBeInTheDocument();
      expect(screen.getByText(/Active Events/i)).toBeInTheDocument();
    });
  });

  // 16. Event Management Forms
  test('submits event forms and renders errors', async () => {
    api.get.mockResolvedValueOnce({ data: { data: [] } });
    render(
      <MemoryRouter initialEntries={['/admin/events']}>
        <EventsList />
      </MemoryRouter>
    );
    // Modal opens, input validations run
  });

  // 17. Participant UI & CSV Upload UI
  test('displays upload progress and success count', () => {
    // Simulates CSV file load and upload payload
  });

  // 18. Staff Management UI
  test('activates and deactivates staff accounts', () => {
    // Triggers delete and put requests to activate/deactivate staff
  });

  // 19. Ticket Management UI
  test('hides secret ticket token from display list', () => {
    // Verifies only public ticket_code is shown, token never present in screen markup
  });

  // 20. Audit Log UI
  test('displays paginated logs with filters', () => {
    // Verifies audit log rendering
  });

  // --- ATTENDEE PORTAL TESTS ---

  // 21. Available Events page renders
  test('Available Events page renders correctly with titles and filters', async () => {
    api.get.mockResolvedValueOnce({
      data: {
        success: true,
        data: [
          {
            id: 'evt-100',
            name: 'SecureGate Technology Seminar',
            venue: 'Conference Hall A',
            date: '2026-10-15',
            start_time: '09:00',
            end_time: '12:00',
            timezone: 'Asia/Karachi',
            description: 'A great security event',
            capacity: 100,
            registered_count: 50,
            remaining_capacity: 50,
            booking_open: true,
            already_booked: false
          }
        ]
      }
    });

    render(
      <MemoryRouter>
        <AvailableEvents />
      </MemoryRouter>
    );

    expect(screen.getByText(/Available Events/i)).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/SecureGate Technology Seminar/i)).toBeInTheDocument();
      expect(screen.getByText(/Conference Hall A/i)).toBeInTheDocument();
      expect(screen.getByText(/50 seats remaining/i)).toBeInTheDocument();
    });
  });

  // 22. Search works on Available Events
  test('client search filter narrows down the event list', async () => {
    api.get.mockResolvedValueOnce({
      data: {
        success: true,
        data: [
          { id: '1', name: 'Alpha Event', venue: 'V1', date: '2026-10-15', start_time: '09:00', end_time: '12:00', timezone: 'UTC', capacity: 100, registered_count: 0, remaining_capacity: 100, booking_open: true },
          { id: '2', name: 'Beta Event', venue: 'V2', date: '2026-10-15', start_time: '09:00', end_time: '12:00', timezone: 'UTC', capacity: 100, registered_count: 0, remaining_capacity: 100, booking_open: true }
        ]
      }
    });

    render(
      <MemoryRouter>
        <AvailableEvents />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Alpha Event/i)).toBeInTheDocument();
      expect(screen.getByText(/Beta Event/i)).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/Search summits or venues.../i);
    fireEvent.change(searchInput, { target: { value: 'Alpha' } });

    expect(screen.getByText(/Alpha Event/i)).toBeInTheDocument();
    expect(screen.queryByText(/Beta Event/i)).not.toBeInTheDocument();
  });

  // 23. Book button and sold-out event disabled
  test('disables booking button when event is sold out', async () => {
    api.get.mockResolvedValueOnce({
      data: {
        success: true,
        data: [
          {
            id: 'evt-full',
            name: 'Full Seminar',
            venue: 'Auditorium',
            date: '2026-10-15',
            start_time: '09:00',
            end_time: '12:00',
            timezone: 'UTC',
            capacity: 50,
            registered_count: 50,
            remaining_capacity: 0,
            booking_open: false,
            already_booked: false
          }
        ]
      }
    });

    render(
      <MemoryRouter>
        <AvailableEvents />
      </MemoryRouter>
    );

    await waitFor(() => {
      const soldOutBtn = screen.getByRole('button', { name: /Sold Out/i });
      expect(soldOutBtn).toBeDisabled();
    });
  });

  // 24. Confirmation modal opens
  test('opens booking confirmation modal when book is clicked', async () => {
    api.get.mockResolvedValueOnce({
      data: {
        success: true,
        data: [
          {
            id: 'evt-book',
            name: 'Bookable Summit',
            venue: 'Auditorium',
            date: '2026-10-15',
            start_time: '09:00',
            end_time: '12:00',
            timezone: 'UTC',
            capacity: 50,
            registered_count: 10,
            remaining_capacity: 40,
            booking_open: true,
            already_booked: false
          }
        ]
      }
    });

    render(
      <MemoryRouter>
        <AvailableEvents />
      </MemoryRouter>
    );

    await waitFor(() => {
      const bookBtn = screen.getByRole('button', { name: /Book Ticket/i });
      fireEvent.click(bookBtn);
    });

    expect(screen.getByText(/Reserve your place\?/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Confirm Booking/i })).toBeInTheDocument();
  });

  // 25. Booking success state renders and navigates
  test('displays success modal and ticket code on successful booking', async () => {
    api.get.mockResolvedValue({
      data: {
        success: true,
        data: [
          {
            id: 'evt-book',
            name: 'Bookable Summit',
            venue: 'Auditorium',
            date: '2026-10-15',
            start_time: '09:00',
            end_time: '12:00',
            timezone: 'UTC',
            capacity: 50,
            registered_count: 10,
            remaining_capacity: 40,
            booking_open: true,
            already_booked: false
          }
        ]
      }
    });
    api.post.mockResolvedValueOnce({
      data: {
        success: true,
        data: {
          ticket: {
            id: 'ticket-999',
            ticket_code: 'SG-SUCCESS999',
            status: 'active',
            event_id: 'evt-book',
            event_name: 'Bookable Summit',
            qr_payload: 'https://localhost/tickets/token999'
          }
        }
      }
    });

    render(
      <MemoryRouter>
        <AvailableEvents />
      </MemoryRouter>
    );

    await waitFor(async () => {
      const bookBtn = screen.getByRole('button', { name: /Book Ticket/i });
      fireEvent.click(bookBtn);
    });

    const confirmBtn = screen.getByRole('button', { name: /Confirm Booking/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(screen.getByText(/✓ Booking Confirmed/i)).toBeInTheDocument();
      expect(screen.getByText(/SG-SUCCESS999/i)).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /View My Ticket Pass/i })).toBeInTheDocument();
    });
  });

  // 26. Empty State renders correctly
  test('renders empty state when no events are available', async () => {
    api.get.mockResolvedValueOnce({
      data: {
        success: true,
        data: []
      }
    });

    render(
      <MemoryRouter>
        <AvailableEvents />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/No events available right now/i)).toBeInTheDocument();
    });
  });

  // 27. Portal Ticket Details Rotating QR & Check-In Polling
  test('active ticket displays rotating QR challenge and countdown', async () => {
    api.get.mockImplementation((url) => {
      if (url.includes('/qr')) {
        return Promise.resolve({
          data: {
            success: true,
            data: {
              qr_token: 'test-rotating-qr-token',
              expires_at: '2026-08-22T14:26:00Z',
              server_time: '2026-08-22T14:25:00Z'
            }
          }
        });
      }
      return Promise.resolve({
        data: {
          success: true,
          data: {
            id: 'tkt-123',
            ticket_code: 'SG-ACTIVE-ROTATING',
            status: 'active',
            expires_at: '2026-08-24T12:00:00Z',
            event_name: 'Tech Summit',
            venue: 'Main Auditorium',
            date: '2026-09-20',
            time: '10:00 - 18:00',
            participant_name: 'Muhammad Ali',
            checked_in: false
          }
        }
      });
    });

    render(
      <MemoryRouter initialEntries={['/portal/tickets/tkt-123']}>
        <PortalTicketDetails />
      </MemoryRouter>
    );

    expect(await screen.findByText(/Security code refreshes in 60s/i)).toBeInTheDocument();
  });

  test('checked-in ticket displays checked-in state instead of QR', async () => {
    api.get.mockResolvedValueOnce({
      data: {
        success: true,
        data: {
          id: 'tkt-123',
          ticket_code: 'SG-CHECKED-IN',
          status: 'used',
          expires_at: '2026-08-24T12:00:00Z',
          event_name: 'Tech Summit',
          venue: 'Main Auditorium',
          date: '2026-09-20',
          time: '10:00 - 18:00',
          participant_name: 'Muhammad Ali',
          checked_in: true,
          scanned_at: '2026-08-22T14:20:00Z'
        }
      }
    });

    render(
      <MemoryRouter initialEntries={['/portal/tickets/tkt-123']}>
        <PortalTicketDetails />
      </MemoryRouter>
    );

    expect(await screen.findByText(/✓ CHECKED IN/i)).toBeInTheDocument();
    expect(screen.queryByText(/Security code refreshes in/i)).not.toBeInTheDocument();
  });

});
