from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import get_db, create_db_and_tables
from models import PullRequest, File, PRStatus
from typing import List

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
