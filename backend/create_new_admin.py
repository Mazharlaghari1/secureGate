from datetime import datetime, timezone

from pymongo import MongoClient
from app.config import settings
from app.security.auth import hash_password


client = MongoClient(settings.MONGO_URI)
db = client[settings.MONGO_DB_NAME]

email = "newadmin@securegate.com"
password = "Admin12345!"
name = "New Admin"

if db.users.find_one({"email": email}):
    print(f"User already exists: {email}")
else:
    now = datetime.now(timezone.utc)

    user = {
        "name": name,
        "email": email.lower(),
        "password_hash": hash_password(password),
        "role": "admin",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }

    db.users.insert_one(user)

    print()
    print("================================")
    print("ADMIN CREATED SUCCESSFULLY")
    print("================================")
    print(f"Email:    {email}")
    print(f"Password: {password}")
    print("Role:     admin")
    print("================================")