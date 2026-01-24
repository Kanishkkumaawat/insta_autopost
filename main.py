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
    
    print(f"Starting InstaForge from {root_dir}...")
    print("Access the dashboard at http://localhost:8000")
    
    # Run the FastAPI app
    # web.main:app initializes the InstaForgeApp and starts background services on startup
    uvicorn.run("web.main:app", host="0.0.0.0", port=8000, reload=True)
