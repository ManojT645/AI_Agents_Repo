from fastapi import FastAPI, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from database import get_db, create_db_and_tables
from models import PullRequest, File, PRStatus
from webhooks import webhook_handler
from typing import List
import json

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

@app.get("/hello")
async def hello_world():
    """Hello world endpoint"""
    return {"message": "Hello, World!"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to PR Review AI Agent", "endpoints": ["/health", "/hello", "/prs", "/prs/{pr_id}"]}

# Database endpoints
@app.get("/prs", response_model=List[PullRequest])
async def get_pull_requests(db: Session = Depends(get_db)):
    """Get all pull requests"""
    return db.query(PullRequest).all()

@app.get("/prs/{pr_id}", response_model=PullRequest)
async def get_pull_request(pr_id: int, db: Session = Depends(get_db)):
    """Get a specific pull request by ID"""
    pr = db.query(PullRequest).filter(PullRequest.id == pr_id).first()
    if not pr:
        return {"error": "Pull request not found"}
    return pr

@app.post("/prs", response_model=PullRequest)
async def create_pull_request(pr: PullRequest, db: Session = Depends(get_db)):
    """Create a new pull request"""
    db.add(pr)
    db.commit()
    db.refresh(pr)
    return pr

@app.get("/prs/{pr_id}/files", response_model=List[File])
async def get_pr_files(pr_id: int, db: Session = Depends(get_db)):
    """Get all files for a specific pull request"""
    files = db.query(File).filter(File.pull_request_id == pr_id).all()
    return files

# GitHub Webhook Endpoint
@app.post("/webhooks/github")
async def github_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle GitHub webhook events"""
    try:
        # Read the request body
        payload_bytes = await request.body()
        payload = json.loads(payload_bytes)
        
        # Verify webhook signature
        if not webhook_handler.verify_signature(request, payload_bytes):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Check if this is a pull request event
        event_type = request.headers.get("X-GitHub-Event")
        if event_type != "pull_request":
            return {"message": f"Event type '{event_type}' not handled", "status": "ignored"}
        
        # Handle the pull request event
        result = await webhook_handler.handle_pull_request_event(payload, db)
        
        return result
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
