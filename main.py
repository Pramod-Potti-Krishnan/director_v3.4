"""
Director Agent - AI Presentation Assistant
Main entry point for the standalone director agent application.

Deployment: 2025-11-08 19:35 UTC - Force redeploy with diagnostic logging
Commits: 976a0cb (comprehensive logging), 62a7e05 (VERSION update)
Features: 📸 📦 📤 🔄 ✅ 💾 emoji markers for log tracing
"""

import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up Google Application Default Credentials from JSON string
# This must happen BEFORE any Google library imports
import json
import tempfile

if os.environ.get('GCP_SERVICE_ACCOUNT_JSON'):
    try:
        credentials_json = os.environ['GCP_SERVICE_ACCOUNT_JSON']

        # Write credentials to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write(credentials_json)
            temp_creds_path = f.name

        # Set GOOGLE_APPLICATION_CREDENTIALS for all Google libraries
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_creds_path
        print(f"✓ Set GOOGLE_APPLICATION_CREDENTIALS to {temp_creds_path}")

    except Exception as e:
        print(f"⚠️  Failed to set up Google credentials: {e}")

# Configure Logfire early in startup
from src.utils.logfire_config import configure_logfire
configure_logfire()

from src.handlers.websocket import WebSocketHandler
from src.utils.logger import setup_logger
from config.settings import get_settings

# Initialize
logger = setup_logger(__name__)
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    logger.info("Starting Director Agent API...")

    # Validate required configurations
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        logger.error("FATAL: Supabase configuration missing!")
        logger.error("Please set the following environment variables in your .env file:")
        logger.error("  SUPABASE_URL=https://your-project.supabase.co")
        logger.error("  SUPABASE_ANON_KEY=your-anon-key-here")
        logger.error("Get these values from your Supabase project settings.")
        raise RuntimeError("Cannot start without Supabase configuration. See logs for details.")

    # Validate AI API keys
    try:
        settings.validate_settings()
        logger.info("✓ AI API key configuration validated")
    except ValueError as e:
        logger.error(f"FATAL: {str(e)}")
        logger.error("Please set at least one of these in your .env file:")
        logger.error("  GOOGLE_API_KEY=your-key-here")
        logger.error("  OPENAI_API_KEY=sk-...")
        logger.error("  ANTHROPIC_API_KEY=sk-ant-...")
        raise RuntimeError("Cannot start without AI API configuration. See logs for details.")

    # Validate Supabase connection
    from src.storage.supabase import get_supabase_client
    try:
        client = get_supabase_client()
        logger.info("✓ Supabase connection validated")
    except Exception as e:
        logger.error(f"FATAL: Failed to connect to Supabase: {str(e)}")
        raise RuntimeError("Cannot start without valid Supabase connection.")

    yield
    logger.info("Shutting down Director Agent API...")

app = FastAPI(
    title="Director Agent API",
    version="1.0.0",
    description="Standalone AI Presentation Assistant - Phase 1 Architecture",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.deckster.xyz",
        "https://deckster.xyz",
        "http://localhost:3000",  # Development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str, user_id: str):
    """Handle WebSocket connections with user authentication."""
    # Validate parameters
    if not session_id or not user_id:
        logger.error("WebSocket connection attempted without session_id or user_id")
        await websocket.close(code=1008, reason="Missing required parameters")
        return

    logger.debug(f"Attempting to initialize WebSocketHandler for session: {session_id}")
    try:
        handler = WebSocketHandler()
        logger.debug("WebSocketHandler initialized successfully")
    except Exception as init_error:
        logger.error(f"Failed to initialize WebSocketHandler: {str(init_error)}", exc_info=True)
        await websocket.close(code=1011, reason="Server error during initialization")
        return

    try:
        await websocket.accept()
        logger.info(f"WebSocket connection established for user: {user_id}, session: {session_id}")

        # Handle the connection
        try:
            await handler.handle_connection(websocket, session_id, user_id)
        except Exception as handler_error:
            logger.error(f"Handler error for user {user_id}, session {session_id}: {str(handler_error)}", exc_info=True)
            raise
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user: {user_id}, session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}, session {session_id}: {str(e)}", exc_info=True)
        # Connection might already be closed, so wrap in try-except
        try:
            if websocket.client_state.value <= 1:  # CONNECTING=0, CONNECTED=1
                await websocket.close()
        except Exception:
            pass  # Ignore close errors

# Health check endpoint
@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "director-agent-api",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "architecture": "Phase 1 - State-Driven with Intent Routing"
    }

# Version verification endpoint
@app.get("/version")
async def version_check():
    """Return deployed code version information."""
    import datetime
    import pathlib

    # Try to read VERSION file (works in Railway where git is not available)
    version_file = pathlib.Path(__file__).parent / "VERSION"
    version_info = {}

    if version_file.exists():
        try:
            with open(version_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if ':' in line:
                        key, value = line.split(':', 1)
                        version_info[key.strip()] = value.strip()
        except Exception as e:
            version_info = {"error": f"Failed to read VERSION file: {str(e)}"}
    else:
        # Fallback: try git (works locally but not in Railway)
        import subprocess
        try:
            git_commit = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'],
                stderr=subprocess.DEVNULL
            ).decode('utf-8').strip()
            version_info = {
                "commit": git_commit[:7],
                "note": "git-based (VERSION file missing)"
            }
        except Exception:
            version_info = {"error": "No VERSION file and git unavailable"}

    return {
        "service": "director-agent-v3.4",
        "version": version_info.get("v3.4-build-20251108-181947", "unknown"),
        "commit": version_info.get("commit", "unknown"),
        "features": version_info.get("features", "unknown"),
        "deployed_status": version_info.get("deployed", "unknown"),
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "environment": settings.APP_ENV,
        "railway_project": os.environ.get('RAILWAY_PROJECT_ID', 'not_on_railway'),
        "version_file_found": version_file.exists()
    }

# Debug endpoint to check Railway environment variables
@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check Railway environment variables."""
    import os
    import pathlib
    google_app_creds = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    creds_file_exists = pathlib.Path(google_app_creds).exists() if google_app_creds else False

    return {
        "RAILWAY_PROJECT_ID": os.environ.get('RAILWAY_PROJECT_ID'),
        "RAILWAY_ENVIRONMENT_NAME": os.environ.get('RAILWAY_ENVIRONMENT_NAME'),
        "RAILWAY_SERVICE_ID": os.environ.get('RAILWAY_SERVICE_ID'),
        "RAILWAY_ENVIRONMENT": os.environ.get('RAILWAY_ENVIRONMENT'),
        "has_gcp_json": bool(os.environ.get('GCP_SERVICE_ACCOUNT_JSON')),
        "is_production_check": os.environ.get('RAILWAY_PROJECT_ID') is not None,
        "settings_is_production": settings.is_production,
        "GOOGLE_APPLICATION_CREDENTIALS": google_app_creds,
        "credentials_file_exists": creds_file_exists
    }

# Test endpoint for WebSocketHandler initialization
@app.get("/test-handler")
async def test_handler():
    """Test WebSocketHandler initialization."""
    try:
        handler = WebSocketHandler()
        return {
            "status": "success",
            "message": "WebSocketHandler initialized successfully",
            "components": {
                "intent_router": handler.intent_router is not None,
                "director": handler.director is not None,
                "sessions": handler.sessions is not None,
                "packager": handler.packager is not None,
                "streamlined_packager": handler.streamlined_packager is not None,
                "workflow": handler.workflow is not None
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"Failed to initialize WebSocketHandler: {str(e)}",
            "error_type": type(e).__name__
        }

# API info endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Director Agent API",
        "description": "Standalone AI-powered presentation generation assistant",
        "version": "1.0.0",
        "architecture": "Phase 1 - State-Driven with Intent-Based Routing",
        "endpoints": {
            "websocket": "/ws?session_id={session_id}&user_id={user_id}",
            "health": "/health",
            "test-handler": "/test-handler"
        },
        "states": [
            "PROVIDE_GREETING",
            "ASK_CLARIFYING_QUESTIONS",
            "CREATE_CONFIRMATION_PLAN",
            "GENERATE_STRAWMAN",
            "REFINE_STRAWMAN"
        ]
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    log_level = "debug" if settings.DEBUG else "info"

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level=log_level,
        reload=settings.DEBUG
    )