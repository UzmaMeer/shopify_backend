from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
import os

# Import Config and Routes
from config import VIDEO_DIR, BASE_PUBLIC_URL
from routes import video, auth, publish, general

app = FastAPI()

# --- Middleware ---
# 1. FIXED: Added your Netlify URL to stop the "SecurityError: Blocked a frame" 
#
origins = [
    "http://localhost:3000",
    "https://addgenerator.netlify.app", 
    BASE_PUBLIC_URL,
    "*" 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

# 2. REQUIRED: Session secret for Authlib and OAuth
app.add_middleware(
    SessionMiddleware, 
    secret_key="UZMA_VIDEO_PROJECT_FINAL_SECRET_999", 
    same_site="lax", 
    https_only=True
)

# 3. REQUIRED: Ensures Railway's HTTPS headers are trusted
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# --- Mount Static Files ---
# ⚠️ Note: On Railway, files created by the worker aren't shared with the backend 
# unless using a Volume. This explains the 404 error.
if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR)
app.mount("/static", StaticFiles(directory=VIDEO_DIR), name="static")

# --- Include Routers ---
app.include_router(video.router)
app.include_router(auth.router)
app.include_router(publish.router)
app.include_router(general.router)

# --- Root Endpoint ---
@app.get("/")
def home(): 
    return RedirectResponse("https://addgenerator.netlify.app")
