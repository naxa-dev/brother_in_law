"""
Database configuration module.

This module sets up the SQLAlchemy engine, session, and base declarative
class used by the application. By isolating these constructs in a single
module we ensure that the rest of the codebase can import a session or
the base class without causing circular imports or duplicating state.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite database URL. The path is relative to the project root; the file
# will be created if it does not already exist. Keeping the database in
# the `db` folder ensures persistence across server restarts when running
# locally. In production you may choose a different path.
SQLITE_DB_PATH = "./db/ax.db"
DATABASE_URL = f"sqlite:///{SQLITE_DB_PATH}"

# The connect_args setting below is required for SQLite when using
# check_same_thread=False. This allows the database session to be used
# across multiple threads, which is necessary for asynchronous web
# frameworks like FastAPI.
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a configured "Session" class and a Session instance. The
# sessionmaker factory is used throughout the application to generate
# database sessions via dependency injection. Sessions are scoped to
# individual requests and disposed of after use.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models. All ORM models should inherit from
# this class so that SQLAlchemy knows how to construct their tables and
# relationships.
Base = declarative_base()