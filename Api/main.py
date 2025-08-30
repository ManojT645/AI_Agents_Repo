from fastapi import FastAPI, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db, create_db_and_tables
from models import PullRequest, File, PRStatus
from webhooks import webhook_handler
from typing import List
import json
import traceback
from pydantic import ValidationError

app = FastAPI(
    title="PR Review AI Agent",
    description="A FastAPI application for PR review with PostgreSQL database",
    version="1.0.0"
)

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    create_db_and_tables()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "Service is healthy"}

@app.get("/db-test")
async def database_connection_test(db: Session = Depends(get_db)):
    """Test database connection and basic operations"""
    try:
        # Test 1: Basic connection
        db.execute(text("SELECT 1"))
        
        # Test 2: Check if tables exist
        result = db.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"))
        table_count = result.scalar()
        
        # Test 3: Check if our specific tables exist
        pr_table_exists = db.execute(text("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'pull_requests')")).scalar()
        files_table_exists = db.execute(text("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'files')")).scalar()
        
        # Test 4: Try to count records (should work even if tables are empty)
        pr_count = db.execute(text("SELECT COUNT(*) FROM pull_requests")).scalar() if pr_table_exists else 0
        files_count = db.execute(text("SELECT COUNT(*) FROM files")).scalar() if files_table_exists else 0
        
        return {
            "status": "success",
            "message": "Database connection test passed",
            "details": {
                "connection": "OK",
                "total_tables": table_count,
                "pull_requests_table": pr_table_exists,
                "files_table": files_table_exists,
                "pull_requests_count": pr_count,
                "files_count": files_count
            }
        }
        
    except Exception as e:
        error_details = {
            "status": "error",
            "message": "Database connection test failed",
            "error": str(e),
            "error_type": type(e).__name__,
            "error_details": {
                "full_traceback": traceback.format_exc(),
                "suggestion": _get_error_suggestion(e)
            }
        }
        
        # Log the full error for debugging
        print(f"Database test error: {error_details}")
        return error_details

def _get_error_suggestion(error: Exception) -> str:
    """Get helpful suggestions based on error type"""
    error_type = type(error).__name__
    
    if "connection" in str(error).lower():
        return "Check if the database is running and accessible. Verify DATABASE_URL in config.env"
    elif "authentication" in str(error).lower() or "password" in str(error).lower():
        return "Check database credentials in DATABASE_URL. Verify username and password"
    elif "does not exist" in str(error).lower():
        return "Database or table does not exist. Run init_db.py to create tables"
    elif "permission" in str(error).lower():
        return "Database user lacks permissions. Check user privileges"
    elif "timeout" in str(error).lower():
        return "Database connection timeout. Check network connectivity and database load"
    else:
        return "Check database configuration and ensure all required packages are installed"

@app.get("/hello")
async def hello_world():
    """Hello world endpoint"""
    return {"message": "Hello, World!"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to PR Review AI Agent", "endpoints": ["/health", "/db-test", "/hello", "/prs", "/prs/{pr_id}"]}

# Database endpoints
@app.get("/prs", response_model=List[PullRequest])
async def get_pull_requests(db: Session = Depends(get_db)):
    """Get all pull requests"""
    try:
        from sqlalchemy import select
        stmt = select(PullRequest)
        result = db.execute(stmt).scalars().all()
        return result
    except Exception as e:
        error_msg = f"Failed to fetch pull requests: {str(e)}"
        print(f"Error in get_pull_requests: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail={
                "error": error_msg,
                "error_type": type(e).__name__,
                "suggestion": "Check database connection and table structure"
            }
        )

@app.get("/prs/{pr_id}", response_model=PullRequest)
async def get_pull_request(pr_id: int, db: Session = Depends(get_db)):
    """Get a specific pull request by ID"""
    try:
        # Validate pr_id
        if pr_id <= 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid PR ID",
                    "message": "PR ID must be a positive integer",
                    "received_value": pr_id
                }
            )
        
        from sqlalchemy import select
        stmt = select(PullRequest).where(PullRequest.id == pr_id)
        pr = db.execute(stmt).scalar_one_or_none()
        
        if not pr:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Pull request not found",
                    "message": f"No pull request found with ID {pr_id}",
                    "suggestion": "Check the PR ID or verify the PR exists in the database"
                }
            )
        return pr
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to fetch pull request {pr_id}: {str(e)}"
        print(f"Error in get_pull_request: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": error_msg,
                "error_type": type(e).__name__,
                "suggestion": "Check database connection and try again"
            }
        )

@app.post("/prs", response_model=PullRequest)
async def create_pull_request(pr: PullRequest, db: Session = Depends(get_db)):
    """Create a new pull request"""
    try:
        # Validate required fields
        if not pr.title or not pr.author or not pr.repository:
            missing_fields = []
            if not pr.title:
                missing_fields.append("title")
            if not pr.author:
                missing_fields.append("author")
            if not pr.repository:
                missing_fields.append("repository")
            
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Missing required fields",
                    "missing_fields": missing_fields,
                    "message": "Title, author, and repository are required fields"
                }
            )
        
        # Check if PR with same number already exists
        from sqlalchemy import select
        existing_stmt = select(PullRequest).where(
            PullRequest.pr_number == pr.pr_number,
            PullRequest.repository == pr.repository
        )
        existing_pr = db.execute(existing_stmt).scalar_one_or_none()
        
        if existing_pr:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "Pull request already exists",
                    "message": f"PR #{pr.pr_number} already exists in repository {pr.repository}",
                    "existing_pr_id": existing_pr.id,
                    "suggestion": "Use PUT method to update existing PR or use a different PR number"
                }
            )
        
        db.add(pr)
        db.commit()
        db.refresh(pr)
        return pr
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        error_msg = f"Failed to create pull request: {str(e)}"
        print(f"Error in create_pull_request: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": error_msg,
                "error_type": type(e).__name__,
                "suggestion": "Check database connection and data validation"
            }
        )

@app.get("/prs/{pr_id}/files", response_model=List[File])
async def get_pr_files(pr_id: int, db: Session = Depends(get_db)):
    """Get all files for a specific pull request"""
    try:
        # Validate pr_id
        if pr_id <= 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid PR ID",
                    "message": "PR ID must be a positive integer",
                    "received_value": pr_id
                }
            )
        
        # First check if PR exists
        from sqlalchemy import select
        pr_stmt = select(PullRequest).where(PullRequest.id == pr_id)
        pr = db.execute(pr_stmt).scalar_one_or_none()
        
        if not pr:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Pull request not found",
                    "message": f"No pull request found with ID {pr_id}",
                    "suggestion": "Check the PR ID or verify the PR exists in the database"
                }
            )
        
        # Get files for the PR
        files_stmt = select(File).where(File.pull_request_id == pr_id)
        files = db.execute(files_stmt).scalars().all()
        return files
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to fetch files for PR {pr_id}: {str(e)}"
        print(f"Error in get_pr_files: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": error_msg,
                "error_type": type(e).__name__,
                "suggestion": "Check database connection and try again"
            }
        )

# GitHub Webhook Endpoint
@app.post("/webhooks/github")
async def github_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle GitHub webhook events"""
    try:
        # Read the request body
        payload_bytes = await request.body()
        
        # Validate payload is not empty
        if not payload_bytes:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Empty payload",
                    "message": "Request body is empty",
                    "suggestion": "Ensure the webhook payload contains valid JSON data"
                }
            )
        
        # Parse JSON payload
        try:
            payload = json.loads(payload_bytes)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid JSON payload",
                    "message": f"Failed to parse JSON: {str(e)}",
                    "received_payload": payload_bytes.decode('utf-8', errors='ignore')[:200] + "..." if len(payload_bytes) > 200 else payload_bytes.decode('utf-8', errors='ignore'),
                    "suggestion": "Ensure the webhook payload is valid JSON"
                }
            )
        
        # Verify webhook signature
        if not webhook_handler.verify_signature(request, payload_bytes):
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "Invalid webhook signature",
                    "message": "GitHub webhook signature verification failed",
                    "suggestion": "Check GITHUB_WEBHOOK_SECRET environment variable and ensure it matches GitHub's webhook secret"
                }
            )
        
        # Check if this is a pull request event
        event_type = request.headers.get("X-GitHub-Event")
        if not event_type:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Missing event type",
                    "message": "X-GitHub-Event header is missing",
                    "suggestion": "Ensure GitHub is sending the correct webhook headers"
                }
            )
        
        if event_type != "pull_request":
            return {
                "message": f"Event type '{event_type}' not handled",
                "status": "ignored",
                "supported_events": ["pull_request"],
                "received_event": event_type
            }
        
        # Validate pull request data
        if "pull_request" not in payload:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Missing pull request data",
                    "message": "Payload does not contain pull_request object",
                    "received_payload_keys": list(payload.keys()),
                    "suggestion": "Ensure this is a valid pull request webhook event"
                }
            )
        
        # Handle the pull request event
        try:
            result = await webhook_handler.handle_pull_request_event(payload, db)
            return result
        except Exception as webhook_error:
            db.rollback()
            error_msg = f"Failed to process webhook event: {str(webhook_error)}"
            print(f"Webhook processing error: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": error_msg,
                    "error_type": type(webhook_error).__name__,
                    "event_type": event_type,
                    "action": payload.get("action", "unknown"),
                    "suggestion": "Check database connection and webhook payload structure"
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Unexpected error in webhook handler: {str(e)}"
        print(f"Unexpected webhook error: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": error_msg,
                "error_type": type(e).__name__,
                "suggestion": "Check server logs for detailed error information"
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
