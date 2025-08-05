"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .utils.errors import ErrorResponse


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Chain Labs Backend API",
        description="Dummy server for frontend integration",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify actual origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Custom exception handler for consistent error format
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Global exception handler for consistent error responses."""
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": 500,
                    "message": "Internal server error"
                }
            }
        )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "message": "Dummy server is running"}
    
    return app


# Import route modules
from .routes import auth, goals, missions, session, chat

# Create the app instance
app = create_app()

# Include routers
app.include_router(auth.router)
app.include_router(goals.router)
app.include_router(missions.router)
app.include_router(session.router)
app.include_router(chat.router)