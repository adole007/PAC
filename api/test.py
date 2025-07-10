# Simple test endpoint for debugging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def test_root():
    return {"message": "Test API is working", "status": "success"}

@app.get("/test")
async def test_endpoint():
    return {"message": "Test endpoint is working", "status": "success"}

# For Vercel compatibility
handler = app
