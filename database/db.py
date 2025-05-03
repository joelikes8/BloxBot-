import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import time
import sqlalchemy.exc

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('database')

# Create base class for models
Base = declarative_base()

# Create engine and session
engine = None
SessionLocal = None

# Maximum retry attempts for database connection
MAX_RETRIES = 5
RETRY_DELAY = 2  # seconds

def get_database_url():
    """Get the database URL from environment variables."""
    # First try to get the full DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        logger.info("Using DATABASE_URL from environment")
        return database_url
    
    # Fallback to building the URL from individual credentials
    db_user = os.getenv("PGUSER", "postgres")
    db_password = os.getenv("PGPASSWORD", "")
    db_host = os.getenv("PGHOST", "localhost")
    db_port = os.getenv("PGPORT", "5432")
    db_name = os.getenv("PGDATABASE", "robloxbot")
    
    constructed_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    logger.info("Constructed database URL from individual credentials")
    return constructed_url

def init_db():
    """Initialize the database connection with retries."""
    global engine, SessionLocal
    
    database_url = get_database_url()
    
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Attempting to connect to database (attempt {attempt+1}/{MAX_RETRIES})")
            
            # Create engine with conservative pool settings
            engine = create_engine(
                database_url,
                pool_pre_ping=True,
                pool_recycle=300,
                connect_args={"connect_timeout": 10},
                pool_size=5,
                max_overflow=10
            )
            
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("Database connection test successful")
            
            # Create session factory
            SessionLocal = scoped_session(
                sessionmaker(autocommit=False, autoflush=False, bind=engine)
            )
            
            # Create all tables
            from database.models import User, Order, Payment, OrderStatus, Notification, Subscription
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
            return
            
        except sqlalchemy.exc.OperationalError as e:
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"Database connection failed: {e}. Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"Database connection failed after {MAX_RETRIES} attempts: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected database error: {e}")
            raise

def get_db():
    """Get database session with connection handling."""
    global SessionLocal
    
    # Initialize database if not already done
    if SessionLocal is None:
        init_db()
    
    # Create a new session
    db = SessionLocal()
    
    try:
        # Test that the connection is working
        db.execute(text("SELECT 1"))
        return db
    except Exception as e:
        db.close()
        logger.error(f"Error getting database session: {e}")
        
        # Try to reinitialize the connection
        try:
            logger.info("Attempting to reinitialize database connection")
            init_db()
            db = SessionLocal()
            return db
        except:
            logger.error("Failed to reconnect to database")
            raise
