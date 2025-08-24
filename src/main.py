"""Main FastAPI application."""

from contextlib import asynccontextmanager
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import init_db

from .utils.errors import ErrorResponse


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""


    app = FastAPI(
        title="Chain Labs Backend API",
        description="Dummy server for frontend integration",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        # lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=(
            r"^http://(localhost|127\.0\.0\.1)(:\d+)?$"
            r"|^https://([a-z0-9-]+\.)+vercel\.app$"
            r"|^https://(www\.)?chainlabs\.in$"
        ),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_process_time_header(request:Request, call_next):
        """Middleware to add process time header."""

        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
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
    

    @app.on_event("startup")
    async def startup_event():
        await init_db.create_tables()
        
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