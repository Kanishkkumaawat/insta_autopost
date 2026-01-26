import uvicorn
import os
import sys

if __name__ == "__main__":
    """
    Entry point for InstaForge.
    Starts the web dashboard and background services.
    """
    # Ensure the current directory is in sys.path so imports work correctly
    root_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, root_dir)
    
    # Production configuration from environment
    PORT = int(os.getenv("PORT", "8000"))
    HOST = os.getenv("HOST", "127.0.0.1")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
    RELOAD = ENVIRONMENT == "development"
    WORKERS = int(os.getenv("WORKERS", "1")) if ENVIRONMENT == "production" else 1
    
    print(f"Starting InstaForge from {root_dir}...")
    print(f"Environment: {ENVIRONMENT}")
    print(f"Access the dashboard at http://{HOST}:{PORT}")
    
    # Run the FastAPI app
    # web.main:app initializes the InstaForgeApp and starts background services on startup
    if ENVIRONMENT == "production" and WORKERS > 1:
        uvicorn.run("web.main:app", host=HOST, port=PORT, workers=WORKERS, log_level="info")
    else:
        uvicorn.run("web.main:app", host=HOST, port=PORT, reload=RELOAD, log_level="info" if ENVIRONMENT == "production" else "debug")
