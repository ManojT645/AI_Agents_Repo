from fastapi import HTTPException, Request
from sqlalchemy.orm import Session
from models import PullRequest, File, PRStatus
from database import get_db
from datetime import datetime, timezone
import json
import hmac
import hashlib
import os
from typing import Dict, Any, List

class GitHubWebhookHandler:
    """Handler for GitHub webhook events"""
    
    def __init__(self, secret_token: str = None):
        self.secret_token = secret_token or os.getenv("GITHUB_WEBHOOK_SECRET", "")
    
    def verify_signature(self, request: Request, payload: bytes) -> bool:
        """Verify GitHub webhook signature"""
        if not self.secret_token:
            return True  # Skip verification if no secret is set
        
        signature = request.headers.get("X-Hub-Signature-256")
        if not signature:
            return False
        
        expected_signature = f"sha256={hmac.new(self.secret_token.encode(), payload, hashlib.sha256).hexdigest()}"
        return hmac.compare_digest(signature, expected_signature)
    
    def parse_pull_request_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse pull request data from GitHub webhook payload"""
        pr_data = payload.get("pull_request", {})
        
        # Map GitHub status to our enum
        status_mapping = {
            "open": PRStatus.OPEN,
            "closed": PRStatus.CLOSED,
            "merged": PRStatus.MERGED
        }
        
        return {
            "title": pr_data.get("title", ""),
            "description": pr_data.get("body", ""),
            "status": status_mapping.get(pr_data.get("state", "open"), PRStatus.OPEN),
            "author": pr_data.get("user", {}).get("login", ""),
            "repository": payload.get("repository", {}).get("full_name", ""),
            "pr_number": pr_data.get("number", 0),
            "github_id": pr_data.get("id"),
            "html_url": pr_data.get("html_url", ""),
            "created_at": datetime.fromisoformat(pr_data.get("created_at", "").replace("Z", "+00:00")),
            "updated_at": datetime.fromisoformat(pr_data.get("updated_at", "").replace("Z", "+00:00"))
        }
    
    def parse_files_data(self, files_data: List[Dict[str, Any]], pr_id: int) -> List[Dict[str, Any]]:
        """Parse files data from GitHub API response"""
        files = []
        for file_data in files_data:
            files.append({
                "filename": file_data.get("filename", ""),
                "file_path": file_data.get("filename", ""),
                "status": file_data.get("status", "modified"),
                "additions": file_data.get("additions", 0),
                "deletions": file_data.get("deletions", 0),
                "changes": file_data.get("changes", 0),
                "pull_request_id": pr_id
            })
        return files
    
    async def handle_pull_request_event(self, payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Handle pull request webhook event"""
        action = payload.get("action")
        
        if action not in ["opened", "synchronize", "reopened", "closed"]:
            return {"message": f"Action '{action}' not handled", "status": "ignored"}
        
        pr_data = self.parse_pull_request_data(payload)
        
        # Check if PR already exists using newer SQLAlchemy 2.0+ syntax
        from sqlalchemy import select
        stmt = select(PullRequest).where(
            PullRequest.pr_number == pr_data["pr_number"],
            PullRequest.repository == pr_data["repository"]
        )
        existing_pr = db.exec(stmt).first()
        
        if existing_pr:
            # Update existing PR
            for key, value in pr_data.items():
                if hasattr(existing_pr, key) and key not in ["id", "pr_number", "repository"]:
                    setattr(existing_pr, key, value)
            existing_pr.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing_pr)
            
            pr_id = existing_pr.id
            message = f"Updated existing PR #{pr_data['pr_number']}"
        else:
            # Create new PR
            new_pr = PullRequest(**pr_data)
            db.add(new_pr)
            db.commit()
            db.refresh(new_pr)
            
            pr_id = new_pr.id
            message = f"Created new PR #{pr_data['pr_number']}"
        
        # Handle files if this is a synchronize event or new PR
        if action in ["opened", "synchronize", "reopened"]:
            # Note: In a real implementation, you would fetch files from GitHub API
            # For now, we'll create a placeholder file entry
            if not existing_pr or action == "synchronize":
                # Remove existing files for this PR if synchronizing
                if existing_pr:
                    delete_stmt = select(File).where(File.pull_request_id == pr_id)
                    existing_files = db.exec(delete_stmt).all()
                    for file in existing_files:
                        db.delete(file)
                
                # Create a placeholder file entry
                placeholder_file = File(
                    filename="files_updated",
                    file_path="files_updated",
                    status="modified",
                    additions=0,
                    deletions=0,
                    changes=0,
                    pull_request_id=pr_id
                )
                db.add(placeholder_file)
                db.commit()
        
        return {
            "message": message,
            "pr_id": pr_id,
            "pr_number": pr_data["pr_number"],
            "action": action,
            "status": "success"
        }

# Create global webhook handler instance
webhook_handler = GitHubWebhookHandler(os.getenv("GITHUB_WEBHOOK_SECRET", ""))
