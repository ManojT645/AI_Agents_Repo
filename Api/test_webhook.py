#!/usr/bin/env python3
"""
Test script to simulate GitHub webhook events
"""
import requests
import json
import hmac
import hashlib
import os
from datetime import datetime

# Configuration
WEBHOOK_URL = "http://localhost:8000/webhooks/github"
SECRET_TOKEN = "test_secret_token"  # Set this to match your GitHub webhook secret

def generate_signature(payload: str, secret: str) -> str:
    """Generate GitHub webhook signature"""
    return f"sha256={hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()}"

def test_pull_request_opened():
    """Test pull request opened event"""
    payload = {
        "action": "opened",
        "pull_request": {
            "id": 123456789,
            "number": 42,
            "title": "Add new feature for user authentication",
            "body": "This PR adds OAuth2 authentication support to the application",
            "state": "open",
            "html_url": "https://github.com/username/repo/pull/42",
            "created_at": "2025-08-26T17:30:00Z",
            "updated_at": "2025-08-26T17:30:00Z",
            "user": {
                "login": "testuser"
            }
        },
        "repository": {
            "full_name": "username/test-repo"
        }
    }
    
    payload_str = json.dumps(payload)
    signature = generate_signature(payload_str, SECRET_TOKEN)
    
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "pull_request",
        "X-Hub-Signature-256": signature
    }
    
    response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
    print(f"Pull Request Opened - Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response

def test_pull_request_synchronize():
    """Test pull request synchronize event (new commits pushed)"""
    payload = {
        "action": "synchronize",
        "pull_request": {
            "id": 123456789,
            "number": 42,
            "title": "Add new feature for user authentication",
            "body": "This PR adds OAuth2 authentication support to the application",
            "state": "open",
            "html_url": "https://github.com/username/repo/pull/42",
            "created_at": "2025-08-26T17:30:00Z",
            "updated_at": "2025-08-26T17:35:00Z",
            "user": {
                "login": "testuser"
            }
        },
        "repository": {
            "full_name": "username/test-repo"
        }
    }
    
    payload_str = json.dumps(payload)
    signature = generate_signature(payload_str, SECRET_TOKEN)
    
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "pull_request",
        "X-Hub-Signature-256": signature
    }
    
    response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
    print(f"Pull Request Synchronize - Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response

def test_pull_request_closed():
    """Test pull request closed event"""
    payload = {
        "action": "closed",
        "pull_request": {
            "id": 123456789,
            "number": 42,
            "title": "Add new feature for user authentication",
            "body": "This PR adds OAuth2 authentication support to the application",
            "state": "closed",
            "html_url": "https://github.com/username/repo/pull/42",
            "created_at": "2025-08-26T17:30:00Z",
            "updated_at": "2025-08-26T17:40:00Z",
            "user": {
                "login": "testuser"
            }
        },
        "repository": {
            "full_name": "username/test-repo"
        }
    }
    
    payload_str = json.dumps(payload)
    signature = generate_signature(payload_str, SECRET_TOKEN)
    
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "pull_request",
        "X-Hub-Signature-256": signature
    }
    
    response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
    print(f"Pull Request Closed - Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response

def test_invalid_signature():
    """Test webhook with invalid signature"""
    payload = {
        "action": "opened",
        "pull_request": {
            "id": 123456789,
            "number": 43,
            "title": "Test PR",
            "body": "Test description",
            "state": "open",
            "html_url": "https://github.com/username/repo/pull/43",
            "created_at": "2025-08-26T17:30:00Z",
            "updated_at": "2025-08-26T17:30:00Z",
            "user": {
                "login": "testuser"
            }
        },
        "repository": {
            "full_name": "username/test-repo"
        }
    }
    
    # Use wrong secret
    payload_str = json.dumps(payload)
    signature = generate_signature(payload_str, "wrong_secret")
    
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "pull_request",
        "X-Hub-Signature-256": signature
    }
    
    response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
    print(f"Invalid Signature - Status: {response.status_code}")
    print(f"Response: {response.text}")
    return response

if __name__ == "__main__":
    print("Testing GitHub Webhook Endpoint")
    print("=" * 50)
    
    # Test 1: Pull Request Opened
    print("\n1. Testing Pull Request Opened Event:")
    test_pull_request_opened()
    
    # Test 2: Pull Request Synchronize
    print("\n2. Testing Pull Request Synchronize Event:")
    test_pull_request_synchronize()
    
    # Test 3: Pull Request Closed
    print("\n3. Testing Pull Request Closed Event:")
    test_pull_request_closed()
    
    # Test 4: Invalid Signature
    print("\n4. Testing Invalid Signature:")
    test_invalid_signature()
    
    print("\n" + "=" * 50)
    print("Webhook testing completed!")
