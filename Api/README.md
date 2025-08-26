# PR Review AI Agent

A FastAPI application for PR review with PostgreSQL database integration.

## Prerequisites

- Python 3.9+
- PostgreSQL 14+

## Setup

### 1. Install PostgreSQL (macOS)
```bash
brew install postgresql@14
brew services start postgresql@14
```

### 2. Create Database
```bash
createdb pr_review_db
```

### 3. Install Python Dependencies
```bash
pip3 install -r requirements.txt
```

### 4. Initialize Database
```bash
python3 init_db.py
```

## Running the Application

### Option 1: Using uvicorn directly
```bash
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Using Python
```bash
python3 main.py
```

## Available Endpoints

### Basic Endpoints
- `GET /` - Root endpoint with welcome message
- `GET /health` - Health check endpoint
- `GET /hello` - Hello world endpoint

### Database Endpoints
- `GET /prs` - Get all pull requests
- `GET /prs/{pr_id}` - Get a specific pull request
- `POST /prs` - Create a new pull request
- `GET /prs/{pr_id}/files` - Get all files for a specific pull request

## Database Schema

### Pull Requests Table
- `id` - Primary key
- `title` - PR title
- `description` - PR description
- `status` - PR status (open, closed, merged)
- `author` - PR author
- `repository` - Repository name
- `pr_number` - Unique PR number
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### Files Table
- `id` - Primary key
- `filename` - File name
- `file_path` - File path
- `status` - File status (added, modified, deleted)
- `additions` - Number of additions
- `deletions` - Number of deletions
- `changes` - Total changes
- `pull_request_id` - Foreign key to pull_requests
- `created_at` - Creation timestamp

## API Documentation

Once the server is running, you can access:
- Interactive API docs: http://localhost:8000/docs
- Alternative API docs: http://localhost:8000/redoc

## Testing

### Basic Endpoints
- http://localhost:8000/health
- http://localhost:8000/hello

### Database Endpoints
- http://localhost:8000/prs (GET all PRs)
- http://localhost:8000/prs/1 (GET specific PR)
- http://localhost:8000/prs/1/files (GET files for PR)

### Create a New PR
```bash
curl -X POST http://localhost:8000/prs \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Fix bug in authentication",
    "description": "This PR fixes a critical bug in the OAuth flow",
    "author": "jane_smith",
    "repository": "my-awesome-app",
    "pr_number": 124
  }'
```
