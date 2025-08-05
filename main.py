"""Entry point for the FastAPI application."""

import os
import uvicorn
from src.main import app


def main():
    """Run the FastAPI application with Uvicorn."""
    # Get port from environment variable (Railway sets this)
    port = int(os.getenv("PORT", 8000))
    
    # Disable reload in production
    is_production = os.getenv("RAILWAY_ENVIRONMENT") is not None
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        reload=not is_production,
        log_level="info"
    )


if __name__ == "__main__":
    main()
