"""
Database connection and session management
Sets up SQLAlchemy with MySQL connection
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import logging
from config import config

# Setup logging
logger = logging.getLogger(__name__)

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    config.DATABASE_URL,
    echo=config.DEBUG,  # Log SQL queries if debug is on
    poolclass=QueuePool,
    pool_size=10,  # Number of connections to keep
    max_overflow=20,  # Extra connections if needed
    pool_pre_ping=True,  # Test connection before using
    pool_recycle=3600  # Recycle connections after 1 hour
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Event listener for connection pool
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set MySQL connection settings"""
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("SET SESSION sql_mode='STRICT_TRANS_TABLES'")
        cursor.close()
        logger.debug("MySQL connection settings applied")
    except Exception as e:
        logger.warning(f"Could not set MySQL connection settings: {e}")

def get_db():
    """
    Dependency injection function for FastAPI
    Provides database session to endpoints
    
    Usage in endpoint:
        @app.get("/endpoint")
        async def endpoint(db: Session = Depends(get_db)):
            # Use db here
            pass
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """
    Initialize database by creating all tables
    Call this once when app starts
    """
    try:
        # Import all models to register them with Base.metadata
        from models import Base
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        return False

def test_db_connection():
    """
    Test if database connection works
    Useful for health checks
    """
    try:
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False