# SecureGate Thesis Terminology Dictionary

To maintain global consistency across all chapters of the thesis, this dictionary defines the standardized terms and naming conventions that must be strictly followed.

---

## 1. Actor Roles and Identifiers

- **Administrator (not Admin)**: A user with administrative privileges. Represents the `admin` role in RBAC. Responsible for event creation, staff management, bulk uploads, and audit log analysis.
- **Staff (not Scanner or Operator)**: A user with check-in privileges. Represents the `staff` role in RBAC. Responsible for processing scanning tickets via webcam and reviewing scan history logs.
- **Attendee (not User or Customer)**: A system client account with registration privileges. Represents the `attendee` role in RBAC. Responsible for profile updates, event booking, and displaying rotating QR ticket codes.
- **Participant (not Guest or Entry)**: A database entry representing a unique registration linking an Attendee's email to a specific Event. Created when an Attendee books an event or when an Administrator imports records.

---

## 2. Technical Terms and Components

- **Dynamic QR Challenge (not QR Code or Rotating Code)**: The cryptographically signed, HMAC-SHA256 JWT containing a unique `jti` nonce and a 60-second expiration timestamp. Generated on demand by the Attendee Portal for check-in verification.
- **Ticket Code (not ID or Number)**: The public-safe alphanumeric string identifier format: `EVT-<random_suffix>`. Used in searches, tables, dashboards, and exported CSV spreadsheets.
- **Secret Token (not Code or Access Key)**: The cryptographically secure, high-entropy token generated via `secrets.token_urlsafe(32)`. Stored in the database and never exposed in standard responses or log collections.
- **Audit Log (not Log Entry or Event Log)**: The structured security document recorded in MongoDB, tracking critical lifecycle actions, actor IDs, targets, timestamps, and redacted metadata.
- **Double Check-in Prevention (not Recheck or Replay Lock)**: The database verification logic employing atomic updates (`find_one_and_update`) under session locks to block duplicate scans from being validated.
- **Soft Deactivation (not Delete or Deletion)**: Setting `is_active` to False instead of running physical SQL/noSQL document deletions. Used for user and participant deactivations to preserve data referential integrity.
