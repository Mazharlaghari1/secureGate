# Smart Web-Based Event Access Backend API

This is the backend API service for the **Smart Web-Based Event Access and QR Ticket Verification System**. It is built with **Python 3.11**, **FastAPI**, **Pydantic**, and **MongoDB (PyMongo)**.

---

## Project Structure
```
backend/
├── app/
│   ├── main.py             # FastAPI entrypoint, middleware configuration
│   ├── config.py           # Environment variables & setting parser
│   ├── database.py         # PyMongo Client connection manager
│   ├── models/             # PyMongo database schema representations
│   ├── schemas/            # Pydantic input/output validation models
│   ├── routers/            # Route controllers (auth, events, tickets, etc.)
│   ├── services/           # Reusable service classes
│   ├── security/           # Token signing and bcrypt algorithms
│   ├── middleware/         # Custom exception handlers & route interceptors
│   ├── utils/              # ObjectId and logging helper utilities
│   └── tests/              # Pytest integration tests
├── requirements.txt        # Backend dependencies
├── .env.example            # Sample configuration template
├── .gitignore              # Files ignored by git
├── Dockerfile              # Docker deployment setup
└── README.md               # Backend documentation
```

---

## Requirements
*   Python 3.11+
*   MongoDB 6.0+ (running locally or via MongoDB Atlas)
*   Docker (Optional, for containerized run)

---

## Getting Started

### 1. Python Environment Setup
We recommend using a virtual environment to manage dependencies:
```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Windows (CMD):
.\venv\Scripts\activate.bat
# On Unix or MacOS:
source venv/bin/activate
```

### 2. Installing Dependencies
Install all required packages from `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root of the backend folder by copying `.env.example`:
```bash
cp .env.example .env
```
Ensure you update the configuration settings inside `.env` (such as `SECRET_KEY`, `MONGO_URI`, and `MONGO_DB_NAME`) for your local setup.

### 4. Starting MongoDB Locally
Make sure MongoDB is running on your machine.
*   **Via MongoDB Community Edition:** Usually runs as a service automatically on `mongodb://localhost:27017`.
*   **Via Docker:**
    ```bash
    docker run -d -p 27017:27017 --name mongodb-local mongo:latest
    ```

### 5. Running the Application
Start the FastAPI server locally using Uvicorn with auto-reload:
```bash
uvicorn app.main:app --reload
```
Once started, the API will be available locally.

---

---

## Authentication & Authorization (RBAC)

The system enforces role-based access control (RBAC) utilizing JSON Web Tokens (JWT) signed with HMAC-SHA256 (`HS256`).

### User Roles
1.  **Admin:** Full administrative capabilities (creating/deactivating staff, event management, participant uploads, ticket actions, and system logs).
2.  **Staff:** Restricted check-in execution (QR scanner access, session scan history, and permitted event viewing).

### CLI Command to Initialize First Admin
Since the system does not use hard-coded default credentials, you must initialize the first administrator account via the CLI script:
```bash
python -m app.utils.create_admin --name "Your Name" --email "admin@example.com" --password "securepassword"
```
This script validates inputs, hashes the password using `bcrypt`, assigns the `admin` role, and saves the user.

### JWT Token Generation & Claims
Access tokens are generated upon successful login at `POST /api/auth/login`. Tokens expire after the duration configured in `ACCESS_TOKEN_EXPIRE_MINUTES` (default 480 minutes).
JWT token claims contain:
*   `sub`: The user's MongoDB database ObjectId (represented as a 24-character hex string).
*   `email`: User login email.
*   `role`: The role (`admin` or `staff`).
*   `exp`: Token expiration time.
*   `iat`: Token issuance time.

**Security Guideline:** Plaintext passwords, password hashes, and sensitive participant info are strictly excluded from token claims.

### Authorization Header Format
To access authenticated endpoints, clients must pass the JWT in the `Authorization` header:
```http
Authorization: Bearer <JWT_ACCESS_TOKEN>
```

### Security Notes
*   **Database-Backed Session Verification:** On every protected API request, the token is decoded, and the user is verified against the database. If a user is deactivated (`is_active = false`), their access is instantly revoked, rendering any unexpired JWT invalid.
*   **User Enumeration Defense:** Login failures return a generic `AUTHENTICATION_FAILED` code without disclosing whether the email exists, the password was incorrect, or the account is deactivated.
*   **No Sensitive Exposure:** Password hashes, secret tokens, and raw keys are strictly redacted from audit logs, database queries, and response models.

---

## Event & Participant Management

The system supports comprehensive Event and Participant lifecycle management with strict access control and validations.

### Event API Endpoints
*   `POST /api/events` (Admin only): Creates a new event. The initial status is set to `draft`.
*   `GET /api/events` (Admin & Staff): Lists events with page navigation, name queries, and filters for `status` or `date`.
*   `GET /api/events/{id}` (Admin & Staff): Returns details of a specific event.
*   `PUT /api/events/{id}` (Admin only): Modifies event parameters, enforcing controlled status transitions.
*   `DELETE /api/events/{id}` (Admin only): Cancels an event (sets status to `cancelled` instead of executing a physical deletion).

### Participant API Endpoints
*   `POST /api/events/{event_id}/participants` (Admin only): Registers a participant under an event.
*   `GET /api/events/{event_id}/participants` (Admin & Staff): Lists registered participants for an event with query filters and page navigation.
*   `GET /api/participants/{id}` (Admin & Staff): Retrieves a participant's profile details.
*   `PUT /api/participants/{id}` (Admin only): Updates participant contact details. Event transfers are prohibited.
*   `DELETE /api/participants/{id}` (Admin only): Deactivates the participant profile (`is_active = False` to protect referential integrity).

### Lifecycle, Timezone, and Registration Rules

*   **Controlled Lifecycle Status Transitions:** Events follow a controlled transition path:
    *   `draft` -> `active` -> `completed`
    *   `draft` -> `cancelled`
    *   `active` -> `cancelled`
    *   Reopening completed events or reactivating cancelled events is prohibited.
*   **Timezone Calculations:** The local inputs `date`, `start_time`, and `end_time` are combined with the provided IANA `timezone` name to parse timezone-aware UTC datetime bounds (`utc_start` and `utc_end`).
*   **Capacity Enforcement:** Enforces `capacity >= 1`. If the count of active participants reaches the event's seating capacity, further enrollments fail with `EVENT_CAPACITY_REACHED` (400).
*   **Duplicate Prevention:** A MongoDB unique index enforces a constraint on `{ event_id: 1, email: 1 }`. Duplicate emails are rejected under the same event, but identical emails are allowed across different events. Email normalization (trim and lowercase) is enforced.
*   **Safe Participant Deactivations:** Deleting a participant switches their active status `is_active = False`. Physical deletion is avoided to ensure downstream ticket and scan history data references remain intact.

---

## CSV Bulk Import & Secure Ticket Generation

The backend provides transaction-safe bulk participant import capabilities alongside secure cryptographic ticket allocations.

### CSV Bulk Import Specs
*   **Endpoint:** `POST /api/events/{event_id}/participants/bulk` (Admin only)
*   **Format:** `multipart/form-data` containing a CSV file.
*   **Required Header Schema:**
    ```csv
    name,email,phone
    ```
*   **Upload Size Limit:** Strictly capped at 2 MB. Larger files return `FILE_TOO_LARGE` (400).
*   **Validation Sequence (All-or-Nothing):**
    1. Size limit checks.
    2. Header field validations.
    3. Row schema checks (Pydantic validation).
    4. Inner-CSV duplicate checking (case-insensitive emails).
    5. Database unique registration collision checks.
    6. Event capacity validation.
    7. Atomic multi-document insertion. Any pipeline failure results in zero imported records.

### Ticket Generation & Revocation
*   **Endpoints:**
    *   `POST /api/events/{event_id}/tickets/generate` (Admin only): Idempotently generates tickets for all active non-ticketed event participants.
    *   `GET /api/events/{event_id}/tickets` (Admin only): Lists tickets with pagination, status filters, and name/email searches. **Excludes secret tokens.**
    *   `POST /api/tickets/{id}/revoke` (Admin only): Manually revokes active tickets. Prevents revocation of used tickets.
*   **Ticket Code vs Secret Token:**
    *   **Ticket Code:** Public-safe unique string format: `EVT-<random_suffix>`. Used in search, logs, dashboards, and export reports.
    *   **Secret Token:** High-entropy secret credential generated via `secrets.token_urlsafe(32)`. Never exposed in admin API payloads, standard logs, or audit records.
*   **Expiration Calculations:** Calculated timezone-safely based on `event.end_time + 2 hours`, stored in UTC. Verified dynamically during ticket reads.

---

## Setup & Deployment Guide

This guide describes how to run and configure the backend and frontend components.

### 1. MongoDB Requirements
A MongoDB connection is required. Standard indexing is applied automatically on startup to ensure fast lookups and uniqueness constraints. Local standalone instances are supported with atomic fallback.

### 2. Environment Variables (`.env`)
Configure the backend `.env` file at the root:
```ini
ENVIRONMENT=development
SECRET_KEY=replace_with_a_secure_cryptographic_random_string
ACCESS_TOKEN_EXPIRE_MINUTES=480
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=event_access_dev
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
MAX_CSV_FILE_SIZE_MB=2
FRONTEND_URL=http://localhost:5173
```

Configure the frontend environment file (`frontend/.env`):
```ini
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Setting Up the Database Admins & Staff
Create the initial administrator account via the backend CLI tool:
```bash
# From backend directory
python -m app.utils.create_admin --name "Your Name" --email "admin@example.com" --password "securepassword"
```
To register staff scanners, sign in as an Admin and call the `POST /api/users/staff` API or use the Admin panel.

### 4. Running the Applications
*   **Run Backend:**
    ```bash
    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8000
    ```
*   **Run Frontend:**
    ```bash
    npm install
    npm run dev
    ```

### 5. Running Tests
*   **Run Backend Pytest:**
    ```bash
    python -m pytest
    ```

---

## Reports & Administration UI

The dashboard provides high-fidelity check-in tracking (Admin role only):

### 1. Global Metrics Panel
Aggregates active/draft events, participant registration counts, and total ticket allocations.

### 2. Timezone-localized Timeline
Displays hourly check-in counts on a visual chart. The scan timestamps are localized using the target event's configured IANA timezone (e.g. `Asia/Karachi` or `UTC`).

### 3. Secure CSV Reports
Provides real-time attendance report downloads. **Secret tokens are strictly redacted** from all files; public ticket codes (`EVT-XXXXXXXX`) are used as safe identification keys.

---

## Public Ticket & Scanner Workflows

### HTTPS Camera Security Rule
Browsers block camera access unless the website is loaded via **HTTPS** or on `localhost`. For production, ensure SSL certificates are configured. For local testing across different mobile devices, use tools like `ngrok` to tunnel the local server via HTTPS.

### Ticket Lifecycle
```text
[Generated] -> Status: active
  ↓ (Scan check-in)
[Checked In] -> Status: used
  ↓ (Manually revoked by Admin)
[Revoked] -> Status: revoked
  ↓ (Event end time + 2 hours passed)
[Expired] -> Status: expired (Evaluated dynamically on read)
```

### Check-in Sequence
1. Staff logs in and selects an active event.
2. Participant presents their ticket QR code.
3. Staff scans the QR (extracting the secret token).
4. Backend executes an atomic update, checks expirations, validates participant status, changes ticket to `used`, and inserts an attendance record.

---

## API Documentation
Interactive API docs are exposed automatically by FastAPI:
*   **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
*   **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
*   **OpenAPI specification JSON:** [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)
