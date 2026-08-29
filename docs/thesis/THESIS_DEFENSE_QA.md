# SecureGate Thesis Defense Q&A

This document compiles 25 simulated thesis examiner questions and their technically defensible answers based strictly on the SecureGate codebase and testing evidence.

---

## 1. System Architecture & Technology Decisions

### Q1: Why did you select MongoDB instead of a relational database like PostgreSQL?
**A:** MongoDB was selected to support high-throughput, low-latency write operations required during rapid gate check-ins. By store ticketing challenges, attendance logs, and participant profiles in document formats, we eliminate expensive SQL JOIN operations. Furthermore, MongoDB supports atomic document-level operations (`find_one_and_update`), which we leveraged to implement double check-in prevention without complex table-level locks.

### Q2: Why did you choose FastAPI over other Python frameworks like Django or Flask?
**A:** FastAPI provides modern asynchronous concurrency support, out-of-the-box OpenAPI documentation, and automatic request validation using Pydantic. It achieves performance comparable to Go and Node.js. Pydantic handles automatic validation of incoming payloads (like CSV formats, email structures, and object IDs), preventing malformed inputs from reaching the database.

### Q3: What is the benefit of using React as a Single Page Application (SPA)?
**A:** React allows us to build a responsive, client-side routed interface. By utilizing React Router DOM, we implement client-side route guards that protect admin, staff, and attendee sections. It also allows us to easily integrate webcam access via `html5-qrcode` for instant, local QR code scanning.

---

## 2. Cryptographic Security & QR Verification

### Q4: How exactly does the dynamic QR code rotation prevent screenshot sharing?
**A:** The QR code does not contain a static ticket ID. Instead, the attendee portal generates an HMAC-SHA256 JWT challenge token signed with the server's `SECRET_KEY`. The token contains:
1. `ticket_id`: Target ticket.
2. `jti`: A unique random hex nonce.
3. `exp`: An expiration timestamp set strictly to 60 seconds from generation.
When scanned, the server decodes the signature, verifies the 60-second limit, and checks the database to ensure the `jti` nonce hasn't been consumed. Any screenshotted or recorded QR code becomes cryptographically invalid after 60 seconds.

### Q5: How do you handle clock drift between the attendee's mobile phone and the server?
**A:** The JWT decoding function in `backend/app/services/attendance.py` specifies a 3-second leeway (`leeway=3`) during verification. This allows for brief network delays and minor desynchronizations. Significant desynchronizations (e.g., client clock set manually) will result in a `QR_EXPIRED` rejection. This is an expected security boundary.

### Q6: How does the system prevent double check-ins if a ticket is scanned at two gates at the exact same millisecond?
**A:** Verification executes an atomic database operation:
```python
updated_challenge = db.ticket_challenges.find_one_and_update(
    {"jti": jti, "status": "issued"},
    {"$set": {"status": "consumed", "consumed_at": scanned_at_time, "consumed_by": current_user["_id"]}}
)
```
Because MongoDB runs this query atomically, only the first request can locate the challenge document with status `"issued"` and update it. The concurrent request will locate no matching document (since status is now `"consumed"`), return `None`, and throw a `TICKET_ALREADY_USED` exception, neutralizing concurrent double check-ins.

### Q7: Why are ticket tokens hidden in the admin endpoints?
**A:** To enforce the principle of least privilege. While administrators generate tickets, they do not need access to the high-entropy secret tokens used to bypass gate verification. The administrative router uses the `TicketResponse` Pydantic schema, which filters out the `token` field, preventing database leaks or insider threats from bypassing check-ins.

### Q8: What is the purpose of the `jti` claim in the QR challenge?
**A:** The `jti` (JWT ID) is a high-entropy hex nonce. When a dynamic QR challenge is issued, the server records the `jti` in the database. During verification, the server checks if the scanned `jti` matches a recorded challenge and has not been marked as consumed. This prevents replay attacks where a user attempts to reuse a captured token within its 60-second lifespan.

---

## 3. Database Integrity & RBAC Security

### Q9: Why did you use soft deactivations (setting `is_active` to False) instead of physical document deletions?
**A:** Hard deletions violate database referential integrity. If we deleted user or participant records, downstream tables like `attendance` and `audit_logs` would contain orphaned foreign keys, corrupting historical metrics. Soft deactivations preserve relational mappings while blocking access immediately.

### Q10: How does the system handle database-backed session validation?
**A:** During RBAC route checking (`get_current_user`), the server decodes the JWT and queries the `users` collection to check if `is_active` is True. If an administrator deactivates a staff member, their active token is rejected on their very next API request, preventing unauthorized access immediately.

### Q11: What database indexes did you implement and why?
**A:** We implemented 13 custom and unique indexes to enforce constraints and speed up lookups:
1. `users`: Unique index on `email` to prevent registration collisions.
2. `participants`: Composite unique index on `{ event_id: 1, email: 1 }` to block duplicate participant enrollments per event.
3. `tickets`: Unique index on `token` and `ticket_code`, and a composite unique index on `{ event_id: 1, participant_id: 1 }` to guarantee a participant receives only one ticket per event.
4. `attendance`: Unique index on `ticket_id` to block double scan inserts.
5. `audit_logs`: Descending index on `timestamp` to optimize administrative security logs.

---

## 4. Bulk Uploads and Reporting

### Q12: How does the bulk CSV import handle errors mid-process?
**A:** In `backend/app/services/participants.py`, the CSV parser executes validations in an all-or-nothing pipeline:
1. Checks that file size is <= 2MB.
2. Verifies header schema matches (`name,email,phone`).
3. Parses rows against Pydantic schemas.
4. Checks for duplicate emails within the CSV.
5. Queries MongoDB to verify that no emails already exist in the event.
6. Assesses event capacity bounds.
If any step fails, the insertion is aborted, resulting in zero database updates and preserving data integrity.

### Q13: How does the reporting module export check-in data?
**A:** The server exports check-in logs using FastAPI's `StreamingResponse`. It queries the `attendance` collection, resolves participant names and ticket codes, format the records into a CSV buffer, and streams it to the admin client. This reduces memory overhead for large exports.

### Q14: How are sensitive parameters redacted from security audit logs?
**A:** The `log_audit` service intercepts metadata payloads, matching keys against a redact list (`password`, `token`, `jwt`, `key`). If a match is found, the value is replaced with `"[REDACTED]"` before database insertion.

---

## 5. Testing and Validation

### Q15: What testing methodology did you apply to verify system security?
**A:** We wrote 113 automated integration and unit test cases using Pytest. The test suite runs against a dedicated local database (`event_access_test`). The tests mock concurrent scanning requests, upload invalid CSV formats, attempt unauthorized IDOR operations, and verify RBAC role permissions.

### Q16: How did you verify the double-scan prevention mechanism during testing?
**A:** We wrote automated tests that simulate concurrent check-in scans. The test issues a single QR challenge, spawns multiple threads, and concurrently sends verification requests to `POST /api/attendance/verify`. The assertions confirm that exactly one scan succeeds (returns 200 VALID) while the duplicate scans are rejected (returns 400 ALREADY_USED).

---

## 6. Implementation & Operational Limits

### Q17: What happens if the entry scanner loses internet connection?
**A:** SecureGate is designed as a cloud-synchronized REST API system, meaning that it requires internet connectivity to execute cryptographic validation and atomic database state updates. An offline scanner is a known limitation. In future work, we propose implementing an offline-first caching protocol.

### Q18: What security protection exists against Insecure Direct Object Reference (IDOR) attacks?
**A:** Endpoints retrieving ticket details (`GET /api/portal/tickets/{id}`) or event bookings verify that the authenticated attendee's email matches the participant email in the target record. If they do not match, the server returns a `403 Forbidden` response.

### Q19: Why does the system combine event date, start time, and timezone to calculate UTC?
**A:** Relying on simple local datetimes results in time-boundary failures when users and events are in different timezones. SecureGate combines local inputs with the IANA timezone string to parse UTC datetimes (`utc_start`, `utc_end`) and stores ticket expirations in UTC, ensuring uniform time checking regardless of the client's local configuration.

### Q20: How are input injection attacks prevented?
**A:** All endpoints utilize Pydantic models with strict typing, minimum/maximum lengths, and regex constraints. MongoDB queries pass parameters as typed variables inside PyMongo dictionary filters, avoiding raw query execution and neutralizing injection attempts.

### Q21: What is the password hashing cost factor and why was it chosen?
**A:** We use Bcrypt with a work factor of 12 rounds. This factor balances security and performance, taking approximately 200-300ms to calculate a hash. This makes dictionary attacks slow while keeping login times responsive for legitimate users.

### Q22: What are the seating capacity constraints enforced during event booking?
**A:** During attendee booking or administrative enrollments, the server counts active participant records under the event. If `count >= capacity`, the request is rejected with an `EVENT_FULL` (400) error, preventing double booking or capacity violations.

### Q23: How do you verify the integrity of imported participant phone numbers?
**A:** The Pydantic parser enforces a regex verification: `max_length=20` and checks for characters. If an administrator imports a phone number with invalid letters or exceeding the limit, the parser throws a validation exception and rolls back the CSV import.

### Q24: What is the lifespan of a JWT access token?
**A:** The access token expiration is set to 480 minutes (8 hours) by default inside `ACCESS_TOKEN_EXPIRE_MINUTES`. This ensures that staff can complete their work shifts without needing to log in repeatedly, while limiting token exposure in case of client device loss.

### Q25: How does the system prevent administrators from deactivating themselves?
**A:** In [`services/users.py:deactivate_staff_user`](file:///c:/Users/mazhar/Desktop/secureGate/backend/app/services/users.py#L142), the server checks if the target `user_id` matches the `current_admin["_id"]`. If they are identical, the deactivation request fails with a `400 Bad Request` error, preventing lockouts.
