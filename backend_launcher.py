#!/usr/bin/env python3
"""
Standalone Backend Launcher for PAC Medical System
This script launches the FastAPI backend in standalone mode.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the current directory to Python path
if hasattr(sys, '_MEIPASS'):
    # Running as PyInstaller bundle
    base_dir = sys._MEIPASS
else:
    # Running as script
    base_dir = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, base_dir)
os.chdir(base_dir)

# Set environment variables for standalone mode
os.environ['STANDALONE_MODE'] = 'true'
os.environ['DISABLE_LIFESPAN'] = 'false'
os.environ['SERVERLESS_MODE'] = 'false'

def main():
    """Main entry point for standalone backend."""
    try:
        # Import and run uvicorn
        import uvicorn
        from backend.server_postgresql_fully_optimized import app
        
        # Get port from command line or environment
        port = int(os.environ.get('PORT', '8002'))
        host = os.environ.get('HOST', '127.0.0.1')
        
        print(f"Starting PAC Backend on {host}:{port}")
        print(f"Database: {os.environ.get('DATABASE_URL', 'Not configured')[:50]}...")
        
        # Run the server
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            server_header=False,
            date_header=False
        )
        
    except KeyboardInterrupt:
        print("Backend shutdown requested")
    except Exception as e:
        print(f"Backend startup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
