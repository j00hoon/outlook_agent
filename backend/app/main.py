# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.emails import router as email_router

# Create FastAPI app
app = FastAPI()

# CORS settings to allow requests from frontend
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # Allowed origins
    allow_credentials=True,     # Allow cookies and credentials
    allow_methods=["*"],        # Allow all HTTP methods
    allow_headers=["*"],        # Allow all headers
)

# Include the email router
app.include_router(email_router)