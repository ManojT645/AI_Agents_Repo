#!/usr/bin/env python3
"""
Database migration script to add enhanced schema columns
for comprehensive PR metadata and code diff information.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment variables")

# Create engine
engine = create_engine(DATABASE_URL)

def migrate_pull_requests_table():
    """Add new columns to pull_requests table"""
    print("Migrating pull_requests table...")
    
    # List of new columns to add
    new_columns = [
        ("branch_name", "VARCHAR(100)"),
        ("base_branch", "VARCHAR(100)"),
        ("commit_sha", "VARCHAR(40)"),
        ("base_commit_sha", "VARCHAR(40)"),
        ("additions", "INTEGER DEFAULT 0"),
        ("deletions", "INTEGER DEFAULT 0"),
        ("changed_files", "INTEGER DEFAULT 0"),
        ("commits_count", "INTEGER DEFAULT 0"),
        ("draft", "BOOLEAN DEFAULT FALSE"),
        ("mergeable", "BOOLEAN"),
        ("rebaseable", "BOOLEAN"),
        ("mergeable_state", "VARCHAR(50)"),
        ("closed_at", "TIMESTAMP"),
        ("merged_at", "TIMESTAMP")
    ]
    
    with engine.connect() as conn:
        for column_name, column_type in new_columns:
            try:
                # Check if column already exists
                result = conn.execute(text(f"""
                    SELECT EXISTS(
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'pull_requests' 
                        AND column_name = '{column_name}'
                    )
                """))
                
                if not result.scalar():
                    print(f"  Adding column: {column_name}")
                    conn.execute(text(f"ALTER TABLE pull_requests ADD COLUMN {column_name} {column_type}"))
                else:
                    print(f"  Column {column_name} already exists, skipping...")
                    
            except Exception as e:
                print(f"  Error adding column {column_name}: {e}")
        
        conn.commit()
        print("  pull_requests table migration completed!")

def migrate_files_table():
    """Add new columns to files table"""
    print("Migrating files table...")
    
    # List of new columns to add
    new_columns = [
        ("sha", "VARCHAR(40)"),
        ("blob_url", "VARCHAR(500)"),
        ("raw_url", "VARCHAR(500)"),
        ("contents_url", "VARCHAR(500)"),
        ("file_size", "INTEGER"),
        ("file_extension", "VARCHAR(20)")
    ]
    
    with engine.connect() as conn:
        for column_name, column_type in new_columns:
            try:
                # Check if column already exists
                result = conn.execute(text(f"""
                    SELECT EXISTS(
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'files' 
                        AND column_name = '{column_name}'
                    )
                """))
                
                if not result.scalar():
                    print(f"  Adding column: {column_name}")
                    conn.execute(text(f"ALTER TABLE files ADD COLUMN {column_name} {column_type}"))
                else:
                    print(f"  Column {column_name} already exists, skipping...")
                    
            except Exception as e:
                print(f"  Error adding column {column_name}: {e}")
        
        conn.commit()
        print("  files table migration completed!")

def main():
    """Run all migrations"""
    print("Starting enhanced schema migration...")
    print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")
    
    try:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ Database connection successful")
        
        # Run migrations
        migrate_pull_requests_table()
        migrate_files_table()
        
        print("\n🎉 Enhanced schema migration completed successfully!")
        print("\nNew columns added:")
        print("pull_requests table:")
        print("  - branch_name, base_branch, commit_sha, base_commit_sha")
        print("  - additions, deletions, changed_files, commits_count")
        print("  - draft, mergeable, rebaseable, mergeable_state")
        print("  - closed_at, merged_at")
        print("\nfiles table:")
        print("  - sha, blob_url, raw_url, contents_url")
        print("  - file_size, file_extension")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    main()
