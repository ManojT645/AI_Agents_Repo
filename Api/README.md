# FastAPI Demo

A simple FastAPI application with health and hello endpoints.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Option 1: Using uvicorn directly
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Using Python
```bash
python main.py
```

## Available Endpoints

- `GET /` - Root endpoint with welcome message
- `GET /health` - Health check endpoint
- `GET /hello` - Hello world endpoint

## API Documentation

Once the server is running, you can access:
- Interactive API docs: http://localhost:8000/docs
- Alternative API docs: http://localhost:8000/redoc

## Testing

Open your browser and navigate to:
- http://localhost:8000/health
- http://localhost:8000/hello
