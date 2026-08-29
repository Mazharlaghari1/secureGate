# SecureGate Thesis Source of Truth

This document serves as the authoritative, verified technical source of truth for the **SecureGate** project. All technical claims, figures, tables, and explanations in the thesis are derived from the contents of this document, which have been forensically verified from the codebase.

---

## 1. Project Identity

- **Project Name**: SecureGate
- **Academic Title**: Smart Web-Based Event Access and QR Ticket Verification System
- **Domain**: Event Management, Cybersecurity, and Physical Access Control
- **Problem Statement**: Traditional event entry systems rely on physical tickets, barcode sheets, or static QR codes. These mechanisms are highly vulnerable to ticket duplication, screenshot sharing, and replay attacks. Furthermore, paper systems lack real-time synchronization, leading to slow check-in queues, manual audit trails, and user role separation failures.
- **Objectives**:
  1. Design and develop a web-based, role-based event management system.
  2. Implement a cryptographically signed, rotating QR challenge ticket mechanism to prevent sharing and duplication.
  3. Enforce real-time verification and prevent double check-ins under race conditions.
  4. Implement database-backed session validation and structured security audit logging with sensitive data redaction.
- **Project Scope**: Single-page application React frontend interfacing with a Python FastAPI REST backend backed by a MongoDB document store.

---

## 2. Technology Stack

| Layer | Technology | Version | Purpose | Evidence (Path in Repository) |
| :--- | :--- | :--- | :--- | :--- |
| **Backend** | Python | 3.13.2 | Core application runtime | Verified via system shell `python --version` |
| **Backend** | FastAPI | 0.138.2 | Web API framework | [`backend/requirements.txt`](file:///c:/Users/mazhar/Desktop/secureGate/backend/requirements.txt#L1) |
| **Backend** | Pydantic | 2.13.4 | Schema validation & Settings management | [`backend/requirements.txt`](file:///c:/Users/mazhar/Desktop/secureGate/backend/requirements.txt#L3-L4) |
| **Backend** | PyMongo | 4.7.3 | MongoDB database driver | [`backend/requirements.txt`](file:///c:/Users/mazhar/Desktop/secureGate/backend/requirements.txt#L5) |
| **Backend** | Bcrypt | 5.0.0 | Cryptographic password hashing | [`backend/requirements.txt`](file:///c:/Users/mazhar/Desktop/secureGate/backend/requirements.txt#L6) |
| **Backend** | PyJWT | 2.13.0 | JSON Web Token signing and decoding | [`backend/requirements.txt`](file:///c:/Users/mazhar/Desktop/secureGate/backend/requirements.txt#L7) |
| **Backend** | Pytest | 9.1.1 | Integration and unit testing framework | [`backend/requirements.txt`](file:///c:/Users/mazhar/Desktop/secureGate/backend/requirements.txt#L8) |
| **Frontend** | React | 18.2.0 | User interface SPA library | [`frontend/package.json`](file:///c:/Users/mazhar/Desktop/secureGate/frontend/package.json#L15-L16) |
| **Frontend** | Vite | 5.0.0 | Frontend build tool and dev server | [`frontend/package.json`](file:///c:/Users/mazhar/Desktop/secureGate/frontend/package.json#L24) |
| **Frontend** | Axios | 1.6.2 | Promise-based HTTP client for API integration | [`frontend/package.json`](file:///c:/Users/mazhar/Desktop/secureGate/frontend/package.json#L12) |
| **Frontend** | html5-qrcode | 2.3.8 | QR code scanning engine for web cameras | [`frontend/package.json`](file:///c:/Users/mazhar/Desktop/secureGate/frontend/package.json#L13) |
| **Frontend** | Tailwind CSS | 3.3.5 | Utility-first CSS styling framework | [`frontend/package.json`](file:///c:/Users/mazhar/Desktop/secureGate/frontend/package.json#L23) |
| **Database** | MongoDB | 6.0+ | Document-based persistence engine | Verified in test config and local running instance |

---

## 3. System Architecture

The SecureGate system employs a client-server architecture separating the browser user interface from the persistence and logic API.

```
       [ Client Browser (React React-Router SPA) ]
                       |
                       | HTTPS REST API Calls (Axios)
                       v
       [ FastAPI Application Gateway (Uvicorn) ]
         |             |                   |
         | Depends     | Middleware        | Services
         v             v                   v
   [ RBAC Auth ] [ Exception Handlers ] [ Service Logic ]
         |             |                   |
         +-------------+-------------------+
                       |
                       | PyMongo Connections
                       v
       [ MongoDB persistence engine (collections) ]
```

- **Authentication Flow**:
  1. The client sends user credentials to `POST /api/auth/login`.
  2. The server authenticates credentials (bcrypt password match) and generates a JWT token containing standard claims (`sub` = ObjectId, `email`, `role`, `exp`, `iat`) signed with HMAC-SHA256.
  3. Subsequent requests pass the token in the `Authorization: Bearer <token>` header.
  4. The `get_current_user` dependency intercepts the request, decodes the token, checks signature validity and expiration, queries the database for user status (`is_active` must be True).
- **Dynamic QR Generation & Verification Flow**:
  1. The attendee requests a ticket QR via `GET /api/portal/tickets/{id}/qr`.
  2. The server verifies ticket ownership and validity, creates a unique one-time `jti` nonce, and signs a dynamic JWT challenge token containing the ticket parameters and a 60-second expiration (`exp = now + 60s`). The challenge is written to `ticket_challenges` as `status = "issued"`.
  3. The frontend displays this token as a QR code and sets a 60-second countdown timer.
  4. The scanner camera (staff user role) reads the QR token, sends it to `POST /api/attendance/verify` along with the matching `event_id`.
  5. The server:
     - Decodes the JWT and validates the cryptographic signature.
     - Enforces the 60-second timeout limit.
     - Matches the target `event_id`.
     - Validates the ticket status (must be `active`, not `used` or `revoked`).
     - Queries `ticket_challenges` to ensure the `jti` is valid and has not been `consumed` (prevents replay/sharing).
     - Processes atomic updates via MongoDB session transactions (or manual fallback) to update `ticket_challenges.status = "consumed"` and `tickets.status = "used"` to eliminate double check-in race conditions.
     - Inserts a record in `attendance` and logs a success audit log.

---

## 4. Verified Feature Inventory

| Feature Area | Sub-Feature | Verification Status | Repository Evidence |
| :--- | :--- | :---: | :--- |
| **Authentication** | User Registration | **VERIFIED** | [`backend/app/routers/auth.py`](file:///c:/Users/mazhar/Desktop/secureGate/backend/app/routers/auth.py#L35) |
| **Authentication** | User Login | **VERIFIED** | [`backend/app/routers/auth.py`](file:///c:/Users/mazhar/Desktop/secureGate/backend/app/routers/auth.py#L21) |
| **Authentication** | Session Lookup | **VERIFIED** | [`backend/app/security/auth.py`](file:///c:/Users/mazhar/Desktop/secureGate/backend/app/security/auth.py#L53) |
| **RBAC** | Admin Authorization | **VERIFIED** | [`backend/app/security/auth.py`](file:///c:/Users/mazhar/Desktop/secureGate/backend/app/security/auth.py#L131) |
| **RBAC** | Staff Authorization | **VERIFIED** | [`backend/app/security/auth.py`](file:///c:/Users/mazhar/Desktop/secureGate/backend/app/security/auth.py#L145) |
| **RBAC** | Attendee Authorization | **VERIFIED** | [`backend/app/security/auth.py`](file:///c:/Users/mazhar/Desktop/secureGate/backend/app/security/auth.py#L159) |
| **Events** | Event Creation | **VERIFIED** | [`backend/app/routers/events.py`](file:///c:/Users/mazhar/Desktop/secureGate/backend/app/routers/events.py#L32) |
| **Events** | Status Transitions | **VERIFIED** | Controlled sequence in [`backend/app/services/events.py`](file:///c:/Users/mazhar/Desktop/secureGate/backend/app/services/events.py) |
| **Events** | Event Cancellation | **VERIFIED** | Set to cancelled, no deletion in [`backend/app/routers/events.py`](file:///c:/Users/mazhar/Desktop/secureGate/backend/app/routers/events.py#L113) |
| **Participants** | Enroll Participant | **VERIFIED** | [`backend/app/routers/participants.py`](file:///c:/Users/mazhar/Desktop/secureGate/backend/app/routers/participants.py#L33) |
| **Participants** | Bulk Import CSV | **VERIFIED** | Limit validation & atomic inserts in [`backend/app/services/participants.py`](file:///c:/Users/mazhar/Desktop/secureGate/backend/app/services/participants.py) |
| **Tickets** | Generate Tickets | **VERIFIED** | Idempotent generation in [`backend/app/services/tickets.py`](file:///c:/Users/mazhar/Desktop/secureGate/backend/app/services/tickets.py) |
| **Tickets** | Revoke Ticket | **VERIFIED** | Set to revoked in [`backend/app/services/tickets.py`](file:///c:/Users/mazhar/Desktop/secureGate/backend/app/services/tickets.py) |
| **Scanning** | Verify QR | **VERIFIED** | JWT verify, leeway, timezone expiry, transaction locks in [`backend/app/services/attendance.py`](file:///c:/Users/mazhar/Desktop/secureGate/backend/app/services/attendance.py#L11) |
| **Reporting** | Dashboard Stats | **VERIFIED** | Calculated database counts in [`backend/app/services/reports.py`](file:///c:/Users/mazhar/Desktop/secureGate/backend/app/services/reports.py) |
| **Reporting** | CSV Check-in Export | **VERIFIED** | Streams attendance records in [`backend/app/routers/reports.py`](file:///c:/Users/mazhar/Desktop/secureGate/backend/app/routers/reports.py#L47) |
| **Audit Logs** | Security Audit Trails | **VERIFIED** | Automatic param redaction in [`backend/app/services/audit.py`](file:///c:/Users/mazhar/Desktop/secureGate/backend/app/services/audit.py#L7) |

---

## 5. Database Schema

The database utilizes MongoDB document collections. The logical structures are enforced by FastAPI schemas and indexed at application startup:

### 1. `users` Collection
- `_id`: ObjectId (Primary Key)
- `email`: string (Unique Index, normalized to lowercase)
- `role`: string (Enum: `admin`, `staff`, `attendee`)
- `name`: string
- `is_active`: boolean (Default: `true`)
- `password_hash`: string (Bcrypt hash)
- `created_at`: datetime
- `updated_at`: datetime

### 2. `events` Collection
- `_id`: ObjectId (Primary Key)
- `name`: string
- `description`: string (Optional)
- `venue`: string
- `date`: string (Format: `YYYY-MM-DD`, Index)
- `start_time`: string (Format: `HH:MM`)
- `end_time`: string (Format: `HH:MM`)
- `timezone`: string (Default: `Asia/Karachi`)
- `capacity`: integer
- `status`: string (Enum: `draft`, `active`, `completed`, `cancelled`, Index)
- `utc_start`: datetime
- `utc_end`: datetime
- `created_at`: datetime
- `updated_at`: datetime

### 3. `participants` Collection
- `_id`: ObjectId (Primary Key)
- `event_id`: ObjectId (Foreign Key referencing `events._id`, Index)
- `name`: string
- `email`: string (Index, Composite Unique Index on `{ event_id: 1, email: 1 }`)
- `phone`: string (Optional)
- `is_active`: boolean
- `created_at`: datetime
- `updated_at`: datetime

### 4. `tickets` Collection
- `_id`: ObjectId (Primary Key)
- `event_id`: ObjectId (Foreign Key referencing `events._id`, Index)
- `participant_id`: ObjectId (Foreign Key referencing `participants._id`, Composite Unique Index `{ event_id: 1, participant_id: 1 }`)
- `ticket_code`: string (Unique Index, public-safe identifier)
- `token`: string (Unique Index, high-entropy secrets token)
- `status`: string (Enum: `active`, `used`, `expired`, `revoked`, Index on `{ event_id, status }`)
- `expires_at`: datetime
- `created_at`: datetime
- `updated_at`: datetime

### 5. `attendance` Collection
- `_id`: ObjectId (Primary Key)
- `event_id`: ObjectId (Foreign Key referencing `events._id`, Composite Index `{ event_id: 1, scanned_at: -1 }`)
- `ticket_id`: ObjectId (Foreign Key referencing `tickets._id`, Unique Index)
- `participant_id`: ObjectId (Foreign Key referencing `participants._id`)
- `scanned_by`: ObjectId (Foreign Key referencing `users._id`, Composite Index `{ scanned_by: 1, scanned_at: -1 }`)
- `scanned_at`: datetime

### 6. `audit_logs` Collection
- `_id`: ObjectId (Primary Key)
- `actor_id`: ObjectId (Optional, Index on `{ actor_id: 1, timestamp: -1 }`)
- `actor_email`: string (Optional)
- `action`: string (Index)
- `target_type`: string
- `target_id`: ObjectId (Optional)
- `status`: string (Enum: `success`, `failure`)
- `metadata`: document (Automatically redacted parameters)
- `timestamp`: datetime (Index, sorted descending)

### 7. `ticket_challenges` Collection
- `_id`: ObjectId (Primary Key)
- `jti`: string (Unique Index, nonce)
- `ticket_id`: ObjectId (Foreign Key referencing `tickets._id`, Index)
- `event_id`: ObjectId
- `issued_at`: datetime
- `expires_at`: datetime (Index)
- `consumed_at`: datetime (Optional)
- `consumed_by`: ObjectId (Optional)
- `status`: string (Enum: `issued`, `consumed`)

---

## 6. API Design

### Authentication
- `POST /api/auth/register` (Public): Registers a new attendee user.
- `POST /api/auth/login` (Public): Authenticates and returns a JWT access token.
- `GET /api/auth/me` (Authenticated): Retrieves detail profile fields of active session.

### Portal (Attendee Actions)
- `GET /api/portal/me` (Attendee): Fetches profile info.
- `PUT /api/portal/profile` (Attendee): Updates name.
- `GET /api/portal/events/available` (Attendee): Lists active events for registration.
- `GET /api/portal/events/available/{event_id}` (Attendee): Retrieves details of active event and booking check.
- `POST /api/portal/events/{event_id}/book` (Attendee): Enrolls attendee in event and generates ticket.
- `GET /api/portal/events` (Attendee): Lists events the attendee is registered for.
- `GET /api/portal/events/{event_id}` (Attendee): Fetches specific event details (with IDOR protection).
- `GET /api/portal/tickets` (Attendee): Lists tickets owned by attendee.
- `GET /api/portal/tickets/{ticket_id}` (Attendee): Fetches ticket details (with IDOR protection).
- `GET /api/portal/tickets/{ticket_id}/qr` (Attendee): Generates rotating QR token JWT (expires in 60s).

### Staff Management (Admin Only)
- `POST /api/users/staff`: Creates staff accounts.
- `GET /api/users/staff`: Paginated listing of staff users.
- `GET /api/users/staff/{id}`: Detailed staff fields.
- `PUT /api/users/staff/{id}`: Edit staff fields (excludes role alterations).
- `DELETE /api/users/staff/{id}`: Deactivates staff user.

### Event Management (Admin/Staff)
- `POST /api/events` (Admin): Creates a draft event.
- `GET /api/events` (Admin/Staff): Paginated lists of events.
- `GET /api/events/{id}` (Admin/Staff): Fetches event details.
- `PUT /api/events/{id}` (Admin): Updates event and manages transitions.
- `DELETE /api/events/{id}` (Admin): Cancels event (status change).

### Participant Management (Admin/Staff)
- `POST /api/events/{event_id}/participants` (Admin): Enrolls participant.
- `GET /api/events/{event_id}/participants` (Admin/Staff): Lists event participants.
- `GET /api/participants/{id}` (Admin/Staff): Fetches participant details.
- `PUT /api/participants/{id}` (Admin): Updates participant details.
- `DELETE /api/participants/{id}` (Admin): Deactivates participant registration.
- `POST /api/events/{event_id}/participants/bulk` (Admin): Import CSV list of participants (Max 2MB).

### Ticket Management (Admin Only)
- `POST /api/events/{event_id}/tickets/generate`: Idempotently generates tickets for all active participants.
- `GET /api/events/{event_id}/tickets`: Lists event tickets (hides tokens).
- `POST /api/tickets/{id}/revoke`: Revokes an active ticket.

### Attendance Check-in (Staff/Admin)
- `POST /api/attendance/verify`: Processes dynamic QR verify scan.
- `GET /api/attendance/my-scans`: Lists recent scans processed by the current user.

### Reporting & Audit (Admin Only)
- `GET /api/reports/dashboard`: Administrative metrics overview.
- `GET /api/reports/event/{event_id}`: Event check-in stats & timeline.
- `GET /api/reports/event/{event_id}/export`: CSV stream download of check-in history.
- `GET /api/audit-logs`: System security audit logs.

---

## 7. Security Architecture

1. **Bcrypt Password Hashing**: Passwords stored as Bcrypt hashes (rounds = 12), protecting against brute-force database leaks.
2. **Access Token Lifecycle**: HMAC-SHA256 JWT tokens. Session details verified on every request against MongoDB `is_active` state.
3. **Dynamic QR Tokenization**: Rotating JWT challenges valid for 60 seconds with strict `jti` single-use replay protection.
4. **Input Size Limits & Validation**: Multipart CSV size capped at 2MB. Strict regex checking for dates, times, emails, and object IDs.
5. **No Hard Deletes**: Soft deactivation of users and participants prevents data corruption of scan logs.
6. **Information Exposure Defense**: Sensitive parameters (tokens, hashes, headers) are redacted from logs and administrative listings.

---

## 8. Verified Test Results

A test suite of **113 integration and foundation test cases** was executed against a test database environment (`event_access_test`). The results are summarized below:

- **Total Test Cases**: 113
- **Passed Cases**: 113
- **Failed Cases**: 0
- **Validation areas**:
  - Health check endpoint response formats.
  - JWT token generation, signatures, and expiration rejection.
  - Database index creation validation.
  - Pydantic validation boundaries (email structure, pagination range, size caps).
  - Multi-user RBAC role validation (staff scan history, admin dashboard, attendee booking filters).
  - Bulk CSV transactional rollback checks under collision.
  - Double check-in atomic transaction check.
