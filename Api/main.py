from fastapi import FastAPI

app = FastAPI(
    title="FastAPI Demo",
    description="A simple FastAPI application with health and hello endpoints",
    version="1.0.0"
)

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
    return {"message": "Welcome to FastAPI Demo", "endpoints": ["/health", "/hello"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
