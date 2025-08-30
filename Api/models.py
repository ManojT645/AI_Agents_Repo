from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum

class PRStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"

class PullRequest(SQLModel, table=True):
    """Pull Request model"""
    __tablename__ = "pull_requests"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=255)
    description: Optional[str] = Field(default=None)
    status: PRStatus = Field(default=PRStatus.OPEN)
    author: str = Field(max_length=100)
    repository: str = Field(max_length=255)
    pr_number: int = Field(unique=True)
    github_id: Optional[int] = Field(default=None)
    html_url: Optional[str] = Field(default=None, max_length=500)
    
    # Enhanced metadata fields
    branch_name: Optional[str] = Field(default=None, max_length=100)
    base_branch: Optional[str] = Field(default=None, max_length=100)
    commit_sha: Optional[str] = Field(default=None, max_length=40)
    base_commit_sha: Optional[str] = Field(default=None, max_length=40)
    
    # Code diff statistics
    additions: Optional[int] = Field(default=0)
    deletions: Optional[int] = Field(default=0)
    changed_files: Optional[int] = Field(default=0)
    commits_count: Optional[int] = Field(default=0)
    
    # GitHub specific fields
    draft: Optional[bool] = Field(default=False)
    mergeable: Optional[bool] = Field(default=None)
    rebaseable: Optional[bool] = Field(default=None)
    mergeable_state: Optional[str] = Field(default=None, max_length=50)
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    closed_at: Optional[datetime] = Field(default=None)
    merged_at: Optional[datetime] = Field(default=None)
    
    # Relationship to files
    files: List["File"] = Relationship(back_populates="pull_request")

class File(SQLModel, table=True):
    """File model for files in pull requests"""
    __tablename__ = "files"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(max_length=500)
    file_path: str = Field(max_length=1000)
    status: str = Field(max_length=20)  # added, modified, deleted
    
    # Code diff details
    additions: int = Field(default=0)
    deletions: int = Field(default=0)
    changes: int = Field(default=0)
    
    # File metadata
    sha: Optional[str] = Field(default=None, max_length=40)
    blob_url: Optional[str] = Field(default=None, max_length=500)
    raw_url: Optional[str] = Field(default=None, max_length=500)
    contents_url: Optional[str] = Field(default=None, max_length=500)
    
    # File type and size info
    file_size: Optional[int] = Field(default=None)
    file_extension: Optional[str] = Field(default=None, max_length=20)
    
    pull_request_id: int = Field(foreign_key="pull_requests.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationship to pull request
    pull_request: Optional[PullRequest] = Relationship(back_populates="files")
