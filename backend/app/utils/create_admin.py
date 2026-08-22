import argparse
import sys
from datetime import datetime
from pymongo.errors import DuplicateKeyError
from app.database import db_manager
from app.security.auth import hash_password

def main():
    parser = argparse.ArgumentParser(description="Create an Initial Admin account.")
    parser.add_argument("--name", required=True, help="Full name of the admin")
    parser.add_argument("--email", required=True, help="Unique email address for login")
    parser.add_argument("--password", required=True, help="Password for login")

    args = parser.parse_args()

    email_normalized = args.email.strip().lower()
    name_stripped = args.name.strip()
    
    if len(name_stripped) < 2:
        print("Error: Name must be at least 2 characters.", file=sys.stderr)
        sys.exit(1)
        
    if len(args.password) < 6:
        print("Error: Password must be at least 6 characters.", file=sys.stderr)
        sys.exit(1)

    try:
        db_manager.connect()
        db = db_manager.get_db()
        db_manager.init_indexes()  # Ensure unique indexes are built
        
        password_hash = hash_password(args.password)
        
        admin_doc = {
            "name": name_stripped,
            "email": email_normalized,
            "password_hash": password_hash,
            "role": "admin",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        db.users.insert_one(admin_doc)
        print(f"Successfully created Admin user: {name_stripped} ({email_normalized})")
    except DuplicateKeyError:
        print(f"Error: A user with email '{email_normalized}' already exists.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Database error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    finally:
        db_manager.close()

if __name__ == "__main__":
    main()
