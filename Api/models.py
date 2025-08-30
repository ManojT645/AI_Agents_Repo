from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship to files
    files: List["File"] = Relationship(back_populates="pull_request")

class File(SQLModel, table=True):
    """File model for files in pull requests"""
    __tablename__ = "files"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(max_length=500)
    file_path: str = Field(max_length=1000)
    status: str = Field(max_length=20)  # added, modified, deleted
    additions: int = Field(default=0)
    deletions: int = Field(default=0)
    changes: int = Field(default=0)
    pull_request_id: int = Field(foreign_key="pull_requests.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship to pull request
    pull_request: Optional[PullRequest] = Relationship(back_populates="files")
