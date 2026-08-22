import logging
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
from app.config import settings

logger = logging.getLogger("event_access")

class DatabaseManager:
    def __init__(self):
        self.client = None
        self.db = None

    def connect(self):
        if self.client is not None:
            return
        
        try:
            logger.info("Initializing MongoDB client...")
            self.client = MongoClient(
                settings.MONGO_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            # Force server selection to verify connectivity
            self.client.admin.command('ping')
            self.db = self.client[settings.MONGO_DB_NAME]
            logger.info(f"Successfully connected to MongoDB database: {settings.MONGO_DB_NAME}")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB at {settings.MONGO_URI}: {str(e)}")
            raise e

    def close(self):
        if self.client:
            logger.info("Closing MongoDB client...")
            self.client.close()
            self.client = None
            self.db = None
            logger.info("MongoDB client closed successfully.")

    def get_db(self):
        if self.db is None:
            self.connect()
        return self.db

    def init_indexes(self):
        db = self.get_db()
        logger.info("Initializing MongoDB indexes...")

        try:
            # 1. users: unique email
            db.users.create_index([("email", ASCENDING)], unique=True)

            # 2. events: date, status
            db.events.create_index([("date", ASCENDING)])
            db.events.create_index([("status", ASCENDING)])

            # 3. participants: unique { event_id: 1, email: 1 }
            db.participants.create_index([("event_id", ASCENDING), ("email", ASCENDING)], unique=True)
            db.participants.create_index([("email", ASCENDING)])

            # 4. tickets: unique token, unique ticket_code, unique { event_id: 1, participant_id: 1 }
            db.tickets.create_index([("token", ASCENDING)], unique=True)
            db.tickets.create_index([("ticket_code", ASCENDING)], unique=True)
            db.tickets.create_index([("event_id", ASCENDING), ("participant_id", ASCENDING)], unique=True)
            db.tickets.create_index([("event_id", ASCENDING), ("status", ASCENDING)])

            # 5. attendance: unique ticket_id, { event_id: 1, scanned_at: -1 }, { scanned_by: 1, scanned_at: -1 }
            db.attendance.create_index([("ticket_id", ASCENDING)], unique=True)
            db.attendance.create_index([("event_id", ASCENDING), ("scanned_at", DESCENDING)])
            db.attendance.create_index([("scanned_by", ASCENDING), ("scanned_at", DESCENDING)])

            # 6. audit_logs: timestamp descending, action, { actor_id: 1, timestamp: -1 }
            db.audit_logs.create_index([("timestamp", DESCENDING)])
            db.audit_logs.create_index([("action", ASCENDING)])
            db.audit_logs.create_index([("actor_id", ASCENDING), ("timestamp", DESCENDING)])

            # 7. ticket_challenges: unique jti, ticket_id, expires_at
            db.ticket_challenges.create_index([("jti", ASCENDING)], unique=True)
            db.ticket_challenges.create_index([("ticket_id", ASCENDING)])
            db.ticket_challenges.create_index([("expires_at", ASCENDING)])

            logger.info("MongoDB indexes initialized successfully.")
        except OperationFailure as e:
            logger.error(f"Error occurred while creating indexes: {str(e)}")
            # We don't crash, but it should be noted
            raise e

db_manager = DatabaseManager()

def get_db():
    return db_manager.get_db()
