"""Test script to verify application imports."""

import sys
import os

# Add the server directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing imports...")

try:
    # Test config
    print("✓ Importing config...")
    from app.config import settings
    print(f"  Environment: {settings.app_env}")

    # Test models
    print("✓ Importing models...")
    from app.models import Topic, Job, Document, Cluster, Summary
    print(f"  Models: {Topic.__name__}, {Job.__name__}, {Document.__name__}, {Cluster.__name__}, {Summary.__name__}")

    # Test schemas
    print("✓ Importing schemas...")
    from app.schemas import TopicCreate, JobCreate, DocumentResponse, ClusterResponse, SummaryResponse
    print(f"  Schemas: {TopicCreate.__name__}, {JobCreate.__name__}, {DocumentResponse.__name__}")

    # Test routers
    print("✓ Importing routers...")
    from app.routers import topics, jobs, documents, clusters, summaries
    print(f"  Routers: topics, jobs, documents, clusters, summaries")

    # Test main app
    print("✓ Importing FastAPI app...")
    from app.main import app
    print(f"  App title: {app.title}")
    print(f"  App version: {app.version}")

    # List all routes
    print("\n✓ Registered routes:")
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(route.methods)
            print(f"  {methods:20s} {route.path}")

    print("\n✅ All imports successful!")
    print("\nApplication is ready to run with:")
    print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")

except Exception as e:
    print(f"\n❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
