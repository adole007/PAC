import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import importlib
import server_postgresql_fully_optimized

# Force reload the module
importlib.reload(server_postgresql_fully_optimized)

# Check if the app has the PUT route
app = server_postgresql_fully_optimized.app

print("Available routes:")
for route in app.routes:
    if hasattr(route, 'methods') and hasattr(route, 'path'):
        print(f"{route.methods} {route.path}")
    elif hasattr(route, 'routes'):  # APIRouter
        for subroute in route.routes:
            if hasattr(subroute, 'methods') and hasattr(subroute, 'path'):
                print(f"{subroute.methods} {subroute.path}")

print("\nLooking specifically for PUT /api/patients/...")
for route in app.routes:
    if hasattr(route, 'routes'):  # APIRouter
        for subroute in route.routes:
            if (hasattr(subroute, 'methods') and 
                hasattr(subroute, 'path') and 
                'PUT' in subroute.methods and 
                '/patients/{patient_id}' in subroute.path):
                print(f"✅ Found PUT endpoint: {subroute.methods} {subroute.path}")
                print(f"Function: {subroute.endpoint.__name__}")
