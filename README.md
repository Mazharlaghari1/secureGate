# SecureGate — Smart Web-Based Event Access & QR Verification System

SecureGate is a production-style event access control and check-in management system featuring high-performance QR code scanning, single-use signed rotating QR challenge tokens (60-second validity), role-based access control (RBAC), and admin/staff management portals.

---

## Repository Structure
```
secureGate/
├── backend/                  # FastAPI & MongoDB Backend API
│   ├── app/                  # Application Source Code
│   ├── .env.example          # Backend Environment Configuration Template
│   ├── requirements.txt      # Python Dependencies
│   └── Dockerfile            # Container deployment file
│
├── frontend/                 # React & Vite Frontend Single-Page Application
│   ├── src/                  # React Source Code
│   ├── .env.example          # Frontend Environment Configuration Template
│   └── package.json          # Node Dependencies & Scripts
│
└── README.md                 # Project Overview & Deployment Documentation (This file)
```

---

## Quick Start (Development & Local LAN Access)

### 1. Network & Firewall Setup (For Cross-Device LAN Testing)
To access the attendee portal from a mobile phone and the staff scanner from a PC, both devices must be on the same Wi-Fi/LAN network.
Run these commands in PowerShell as **Administrator** on the host PC (with LAN IP e.g., `10.241.246.90`) to allow connections on Vite and FastAPI ports:
```powershell
New-NetFirewallRule -DisplayName "SecureGate Backend API" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow -Profile Private
New-NetFirewallRule -DisplayName "SecureGate Frontend Vite" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow -Profile Private
```

### 2. Backend API Startup
1. Navigate to `backend` directory and activate the python virtual environment:
   ```bash
   cd backend
   python -m venv .venv
   # Windows PowerShell:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```
2. Install Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy environment configuration:
   ```bash
   copy .env.example .env
   ```
4. Start FastAPI:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
*   **Local Docs & Swagger URL**: http://localhost:8000/docs
*   **LAN Docs & Swagger URL**: http://10.241.246.90:8000/docs

### 3. Frontend App Startup
1. Navigate to `frontend` directory:
   ```bash
   cd ../frontend
   npm install
   ```
2. Copy environment configuration:
   ```bash
   copy .env.example .env
   ```
   Set `VITE_API_BASE_URL=http://10.241.246.90:8000` (pointing to the backend LAN address).
3. Start Vite dev server binding to wildcard host:
   ```bash
   npm run dev
   ```
*   **Local Web App URL**: http://localhost:5173
*   **LAN Web App URL**: http://10.241.246.90:5173

---

## Production Deployment Recommendations

### 1. Security & HTTPS (Critical)
*   **Mandatory HTTPS**: In production, the scanner relies on the HTML5 Camera API (`html5-qrcode`), which is only permitted by web browsers under secure origins (`https://` or `localhost`). Set up SSL certificates via Let's Encrypt / Certbot.
*   **Reverse Proxy**: Deploy a reverse proxy (e.g. Nginx or Traefik) in front of the application to handle TLS termination, serve frontend static files, and forward `/api` requests to the Uvicorn application.

### 2. Production Environment Configurations
Ensure these environment variables are set in your production host environment:

#### Backend Settings
*   `ENVIRONMENT`: Set to `production`.
*   `SECRET_KEY`: A secure random cryptographic string (e.g., generated via `openssl rand -hex 32`).
*   `MONGO_URI`: Production MongoDB connection string (with user authentication, SSL/TLS enabled).
*   `ALLOWED_ORIGINS`: JSON array of allowed origins, e.g. `["https://securegate.example.com"]`.
*   `FRONTEND_URL`: Public-facing domain name of the frontend app, e.g. `https://securegate.example.com` (this is encoded into ticket QR references).

#### Frontend Settings
*   `VITE_API_BASE_URL`: Public-facing API URL, e.g. `https://securegate.example.com/api` (or separate API subdomains).

---

## Automated QA Verification Run
*   To verify backend schemas, check-in validation, and security permissions:
    ```bash
    cd backend
    .venv\Scripts\activate
    python -m pytest
    ```
*   To compile frontend production bundles:
    ```bash
    cd frontend
    npm run build
    ```
