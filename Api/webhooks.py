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
import traceback

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
        try:
            pr_data = payload.get("pull_request", {})
            
            if not pr_data:
                raise ValueError("Pull request data is missing or empty")
            
            # Map GitHub status to our enum
            status_mapping = {
                "open": PRStatus.OPEN,
                "closed": PRStatus.CLOSED,
                "merged": PRStatus.MERGED
            }
            
            # Parse and validate required fields
            title = pr_data.get("title", "")
            if not title:
                raise ValueError("Pull request title is missing")
            
            author = pr_data.get("user", {}).get("login", "")
            if not author:
                raise ValueError("Pull request author is missing")
            
            repository = payload.get("repository", {}).get("full_name", "")
            if not repository:
                raise ValueError("Repository information is missing")
            
            pr_number = pr_data.get("number")
            if pr_number is None:
                raise ValueError("Pull request number is missing")
            
            # Parse dates with error handling
            try:
                created_at = datetime.fromisoformat(pr_data.get("created_at", "").replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                created_at = datetime.now(timezone.utc)
                print(f"Warning: Could not parse created_at, using current time for PR #{pr_number}")
            
            try:
                updated_at = datetime.fromisoformat(pr_data.get("updated_at", "").replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                updated_at = datetime.now(timezone.utc)
                print(f"Warning: Could not parse updated_at, using current time for PR #{pr_number}")
            
            # Parse optional dates
            closed_at = None
            merged_at = None
            
            if pr_data.get("closed_at"):
                try:
                    closed_at = datetime.fromisoformat(pr_data.get("closed_at", "").replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    print(f"Warning: Could not parse closed_at for PR #{pr_number}")
            
            if pr_data.get("merged_at"):
                try:
                    merged_at = datetime.fromisoformat(pr_data.get("merged_at", "").replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    print(f"Warning: Could not parse merged_at for PR #{pr_number}")
            
            # Extract branch information
            head = pr_data.get("head", {})
            base = pr_data.get("base", {})
            
            branch_name = head.get("ref", "")
            base_branch = base.get("ref", "")
            commit_sha = head.get("sha", "")
            base_commit_sha = base.get("sha", "")
            
            # Extract code diff statistics
            additions = pr_data.get("additions", 0)
            deletions = pr_data.get("deletions", 0)
            changed_files = pr_data.get("changed_files", 0)
            commits_count = pr_data.get("commits", 0)
            
            # Extract GitHub specific fields
            draft = pr_data.get("draft", False)
            mergeable = pr_data.get("mergeable")
            rebaseable = pr_data.get("rebaseable")
            mergeable_state = pr_data.get("mergeable_state")
            
            return {
                "title": title,
                "description": pr_data.get("body", ""),
                "status": status_mapping.get(pr_data.get("state", "open"), PRStatus.OPEN),
                "author": author,
                "repository": repository,
                "pr_number": pr_number,
                "github_id": pr_data.get("id"),
                "html_url": pr_data.get("html_url", ""),
                
                # Enhanced metadata
                "branch_name": branch_name,
                "base_branch": base_branch,
                "commit_sha": commit_sha,
                "base_commit_sha": base_commit_sha,
                
                # Code diff statistics
                "additions": additions,
                "deletions": deletions,
                "changed_files": changed_files,
                "commits_count": commits_count,
                
                # GitHub specific fields
                "draft": draft,
                "mergeable": mergeable,
                "rebaseable": rebaseable,
                "mergeable_state": mergeable_state,
                
                # Timestamps
                "created_at": created_at,
                "updated_at": updated_at,
                "closed_at": closed_at,
                "merged_at": merged_at
            }
            
        except Exception as e:
            raise ValueError(f"Failed to parse pull request data: {str(e)}")
    
    def parse_files_data(self, files_data: List[Dict[str, Any]], pr_id: int) -> List[Dict[str, Any]]:
        """Parse files data from GitHub API response"""
        files = []
        for file_data in files_data:
            # Extract file extension
            filename = file_data.get("filename", "")
            file_extension = ""
            if filename and "." in filename:
                file_extension = filename.split(".")[-1]
            
            files.append({
                "filename": filename,
                "file_path": file_data.get("filename", ""),
                "status": file_data.get("status", "modified"),
                "additions": file_data.get("additions", 0),
                "deletions": file_data.get("deletions", 0),
                "changes": file_data.get("changes", 0),
                
                # Enhanced file metadata
                "sha": file_data.get("sha"),
                "blob_url": file_data.get("blob_url"),
                "raw_url": file_data.get("raw_url"),
                "contents_url": file_data.get("contents_url"),
                "file_size": file_data.get("size"),
                "file_extension": file_extension,
                
                "pull_request_id": pr_id
            })
        return files
    
    async def handle_pull_request_event(self, payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Handle pull request webhook event"""
        try:
            action = payload.get("action")
            
            if not action:
                raise ValueError("Missing 'action' field in webhook payload")
            
            if action not in ["opened", "synchronize", "reopened", "closed"]:
                return {
                    "message": f"Action '{action}' not handled",
                    "status": "ignored",
                    "supported_actions": ["opened", "synchronize", "reopened", "closed"],
                    "received_action": action
                }
            
            # Parse pull request data
            try:
                pr_data = self.parse_pull_request_data(payload)
            except Exception as parse_error:
                raise ValueError(f"Failed to parse pull request data: {str(parse_error)}")
            
            # Validate required fields
            required_fields = ["title", "author", "repository", "pr_number"]
            missing_fields = [field for field in required_fields if not pr_data.get(field)]
            
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")
            
            # Check if PR already exists using correct SQLAlchemy 2.0+ syntax
            from sqlalchemy import select
            stmt = select(PullRequest).where(
                PullRequest.pr_number == pr_data["pr_number"],
                PullRequest.repository == pr_data["repository"]
            )
            existing_pr = db.execute(stmt).scalar_one_or_none()
            
            if existing_pr:
                # Update existing PR
                try:
                    for key, value in pr_data.items():
                        if hasattr(existing_pr, key) and key not in ["id", "pr_number", "repository"]:
                            setattr(existing_pr, key, value)
                    existing_pr.updated_at = datetime.now(timezone.utc)
                    db.commit()
                    db.refresh(existing_pr)
                    
                    pr_id = existing_pr.id
                    message = f"Updated existing PR #{pr_data['pr_number']}"
                except Exception as update_error:
                    db.rollback()
                    raise ValueError(f"Failed to update existing PR: {str(update_error)}")
            else:
                # Create new PR
                try:
                    new_pr = PullRequest(**pr_data)
                    db.add(new_pr)
                    db.commit()
                    db.refresh(new_pr)
                    
                    pr_id = new_pr.id
                    message = f"Created new PR #{pr_data['pr_number']}"
                except Exception as create_error:
                    db.rollback()
                    raise ValueError(f"Failed to create new PR: {str(create_error)}")
            
            # Handle files if this is a synchronize event or new PR
            if action in ["opened", "synchronize", "reopened"]:
                try:
                    # Note: In a real implementation, you would fetch files from GitHub API
                    # For now, we'll create a placeholder file entry
                    if not existing_pr or action == "synchronize":
                        # Remove existing files for this PR if synchronizing
                        if existing_pr:
                            delete_stmt = select(File).where(File.pull_request_id == pr_id)
                            existing_files = db.execute(delete_stmt).scalars().all()
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
                except Exception as file_error:
                    db.rollback()
                    # Log the error but don't fail the entire operation
                    print(f"Warning: Failed to handle files for PR {pr_id}: {str(file_error)}")
            
            return {
                "message": message,
                "pr_id": pr_id,
                "pr_number": pr_data["pr_number"],
                "action": action,
                "status": "success",
                "details": {
                    "repository": pr_data["repository"],
                    "author": pr_data["author"],
                    "title": pr_data["title"]
                }
            }
            
        except Exception as e:
            # Log the full error for debugging
            print(f"Error in handle_pull_request_event: {traceback.format_exc()}")
            raise ValueError(f"Webhook processing failed: {str(e)}")

# Create global webhook handler instance
webhook_handler = GitHubWebhookHandler(os.getenv("GITHUB_WEBHOOK_SECRET", ""))
