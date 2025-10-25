"""
Database migration script: Add registry fields to Project model
Run this script once to add new columns from Excel registry integration
"""
import sqlite3
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent.parent / "pm_tool.db"

def migrate():
    """Add new registry fields to projects table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🔄 Starting migration: Add registry fields to projects table...")

    # List of new columns to add
    new_columns = [
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

    # Add each column if it doesn't exist
    for column_name, column_type in new_columns:
        try:
            cursor.execute(f"ALTER TABLE projects ADD COLUMN {column_name} {column_type}")
            print(f"  ✅ Added column: {column_name} ({column_type})")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"  ⏭️  Column already exists: {column_name}")
            else:
                print(f"  ❌ Error adding column {column_name}: {e}")

    conn.commit()
    conn.close()

    print("✅ Migration completed successfully!")
    print("\n📋 Summary:")
    print(f"   - Added {len(new_columns)} new columns to projects table")
    print("   - Database path:", DB_PATH)


if __name__ == "__main__":
    migrate()
