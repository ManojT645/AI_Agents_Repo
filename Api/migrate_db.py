#!/usr/bin/env python3
"""
Database migration script to add GitHub-related columns
"""
from database import engine, SessionLocal
from sqlalchemy import text

def migrate_database():
    """Add new columns to the pull_requests table"""
    db = SessionLocal()
    
    try:
        # Check if columns already exist
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'pull_requests' 
            AND column_name IN ('github_id', 'html_url')
        """))
        existing_columns = [row[0] for row in result.fetchall()]
        
        print("Existing columns:", existing_columns)
        
        # Add github_id column if it doesn't exist
        if 'github_id' not in existing_columns:
            print("Adding github_id column...")
            db.execute(text("ALTER TABLE pull_requests ADD COLUMN github_id INTEGER"))
            print("✓ Added github_id column")
        
        # Add html_url column if it doesn't exist
        if 'html_url' not in existing_columns:
            print("Adding html_url column...")
            db.execute(text("ALTER TABLE pull_requests ADD COLUMN html_url VARCHAR(500)"))
            print("✓ Added html_url column")
        
        db.commit()
        print("Database migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_database()
