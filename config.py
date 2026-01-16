import os

# --- SHARED VOLUME PATH ---
# Railway Volume Mount Path: /app/video
VIDEO_DIR = "/app/video" 

# Ensure the directory exists inside the volume
if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR, exist_ok=True)

# --- PUBLIC URL ---
# Note: Isay ensure karein ke yeh aapka latest domain hai
BASE_PUBLIC_URL = "https://snakiest-edward-autochthonously.ngrok-free.dev"

# --- API KEYS ---
SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_API_SECRET = os.getenv("SHOPIFY_API_SECRET")
META_CLIENT_ID = os.getenv("META_CLIENT_ID")
META_CLIENT_SECRET = os.getenv("META_CLIENT_SECRET")
IG_USER_ID = os.getenv("IG_USER_ID")
TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
