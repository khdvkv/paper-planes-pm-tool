"""
Database connection and session management
"""
import os
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

from database.models import Base

# Load environment variables
load_dotenv()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pm_tool.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False  # Set to True for SQL query logging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def run_migrations():
    """Run database migrations - add missing columns to existing tables"""
    # Only run migrations for SQLite databases
    if "sqlite" not in DATABASE_URL:
        return

    # Extract database path from URL
    db_path = DATABASE_URL.replace("sqlite:///", "").replace("./", "")

    # Ensure absolute path
    if not os.path.isabs(db_path):
        db_path = os.path.abspath(db_path)

    # Check if database file exists
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if projects table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'")
    if not cursor.fetchone():
        conn.close()
        return

    print("🔄 Running database migrations...")

    # Registry fields migration - Add new columns to projects table
    registry_columns = [
        # Document links
        ("contract_appendix_url", "TEXT"),
        ("problem_map_url", "TEXT"),
        ("adminscale_url", "TEXT"),
        ("pert_url", "TEXT"),

        # Timeline fields
        ("ideal_phase_end_date", "DATE"),
        ("phase_duration_weeks", "INTEGER"),
        ("contract_phase_end_date", "DATE"),
        ("ideal_project_end_date", "DATE"),
        ("contract_project_end_date", "DATE"),

        # Buffer fields
        ("days_to_real_phase_end", "INTEGER"),
        ("days_to_ideal_phase_end", "INTEGER"),
        ("days_to_phase_end_no_buffer", "INTEGER"),
        ("phase_buffer_days", "INTEGER"),
        ("project_buffer_days", "INTEGER"),
    ]

    migrations_applied = 0

    for column_name, column_type in registry_columns:
        try:
            cursor.execute(f"ALTER TABLE projects ADD COLUMN {column_name} {column_type}")
            print(f"  ✅ Added column: {column_name}")
            migrations_applied += 1
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                # Column already exists, skip silently
                pass
            else:
                print(f"  ⚠️  Error adding column {column_name}: {e}")

    conn.commit()
    conn.close()

    if migrations_applied > 0:
        print(f"✅ Applied {migrations_applied} migrations")
    else:
        print("✅ Database schema is up to date")


def init_db():
    """Initialize database - create all tables and run migrations"""
    Base.metadata.create_all(bind=engine)
    run_migrations()
    print("✅ Database initialized successfully!")


def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Session will be closed by caller


def drop_all_tables():
    """Drop all tables - use with caution!"""
    Base.metadata.drop_all(bind=engine)
    print("⚠️ All tables dropped!")


# Run migrations immediately when module is imported
# This ensures existing databases get updated before any queries happen
run_migrations()
