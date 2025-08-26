#!/usr/bin/env python3
"""
Database initialization script
"""
from database import create_db_and_tables, SessionLocal
from models import PullRequest, File, PRStatus
from datetime import datetime

def init_database():
    """Initialize database and create tables"""
    print("Creating database tables...")
    create_db_and_tables()
    print("Database tables created successfully!")

def insert_test_data():
    """Insert test data into the database"""
    db = SessionLocal()
    
    try:
        # Create a test pull request
        test_pr = PullRequest(
            title="Add new feature for user authentication",
            description="This PR adds OAuth2 authentication support to the application",
            status=PRStatus.OPEN,
            author="john_doe",
            repository="my-awesome-app",
            pr_number=123
        )
        
        db.add(test_pr)
        db.commit()
        db.refresh(test_pr)
        
        print(f"Created test PR with ID: {test_pr.id}")
        
        # Create test files for the PR
        test_files = [
            File(
                filename="auth.py",
                file_path="src/auth/auth.py",
                status="added",
                additions=150,
                deletions=0,
                changes=150,
                pull_request_id=test_pr.id
            ),
            File(
                filename="models.py",
                file_path="src/models/user.py",
                status="modified",
                additions=25,
                deletions=10,
                changes=35,
                pull_request_id=test_pr.id
            ),
            File(
                filename="config.py",
                file_path="src/config/oauth.py",
                status="added",
                additions=80,
                deletions=0,
                changes=80,
                pull_request_id=test_pr.id
            )
        ]
        
        for file in test_files:
            db.add(file)
        
        db.commit()
        print(f"Created {len(test_files)} test files")
        
        # Query and display the test data
        print("\n=== Test Data Verification ===")
        
        # Query the PR
        pr = db.query(PullRequest).filter(PullRequest.pr_number == 123).first()
        if pr:
            print(f"PR Found: {pr.title}")
            print(f"Status: {pr.status}")
            print(f"Author: {pr.author}")
            print(f"Files count: {len(pr.files)}")
            
            for file in pr.files:
                print(f"  - {file.filename} ({file.status}): +{file.additions} -{file.deletions}")
        
        print("\nDatabase initialization completed successfully!")
        
    except Exception as e:
        print(f"Error during database initialization: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
    insert_test_data()
