"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import topics, jobs, documents, clusters, summaries

app = FastAPI(
    title="Discourse Radar API",
    description="First-Person Discourse Scout - Agentic SaaS",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.client_url, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(topics.router)
app.include_router(jobs.router)
app.include_router(documents.router)
app.include_router(clusters.router)
app.include_router(summaries.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.app_env,
        "version": "0.1.0"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Discourse Radar API",
        "docs": "/docs",
        "health": "/health"
    }
