"""
Database connection management
"""

import os
from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine as sa_create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from ..config import Config, get_data_dir
from ..utils.logging import get_logger

logger = get_logger(__name__)


def get_database_url(config: Optional[Config] = None) -> str:
    """
    Get database URL from configuration
    
    Args:
        config: Configuration object, if None will load from environment
        
    Returns:
        Database URL string
    """
    if config and config.database_url:
        return config.database_url
    
    # Default to SQLite database in data directory
    if config:
        db_path = config.database_path
    else:
        db_path = os.getenv("XBRL_DATABASE_PATH", "financial_data.db")
    
    # Ensure absolute path
    if not os.path.isabs(db_path):
        data_dir = get_data_dir()
        db_path = data_dir / db_path
    
    # Ensure parent directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    return f"sqlite:///{db_path}"


def create_engine(database_url: Optional[str] = None, config: Optional[Config] = None) -> Engine:
    """
    Create SQLAlchemy engine
    
    Args:
        database_url: Database URL, if None will be determined from config
        config: Configuration object
        
    Returns:
        SQLAlchemy Engine instance
    """
    if not database_url:
        database_url = get_database_url(config)
    
    logger.info(f"Creating database engine for: {database_url}")
    
    # SQLite-specific configuration
    if database_url.startswith("sqlite"):
        engine = sa_create_engine(
            database_url,
            poolclass=StaticPool,
            connect_args={
                "check_same_thread": False,  # Allow multi-threading
                "timeout": 30,  # 30 second timeout
            },
            echo=False  # Set to True for SQL debugging
        )
    else:
        # PostgreSQL or other databases
        engine = sa_create_engine(
            database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False
        )
    
    return engine


def get_session(engine: Engine) -> Session:
    """
    Create database session
    
    Args:
        engine: SQLAlchemy engine
        
    Returns:
        SQLAlchemy Session instance
    """
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


class DatabaseConnection:
    """
    Database connection manager with context manager support
    """
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config
        self.engine: Optional[Engine] = None
        self.session: Optional[Session] = None
    
    def __enter__(self) -> Session:
        """Enter context manager"""
        self.engine = create_engine(config=self.config)
        self.session = get_session(self.engine)
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager"""
        if self.session:
            if exc_type is None:
                self.session.commit()
            else:
                self.session.rollback()
            self.session.close()
        
        if self.engine:
            self.engine.dispose()