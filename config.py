import os

# --- SHARED STORAGE (RAILWAY VOLUME) ---
# ❌ Puraana (Relative): os.path.dirname(os.path.abspath(__file__))
# ✅ Naya (Absolute): Yeh path aapke Railway Volume 'Mount Path' se match karta hai
VIDEO_DIR = "/app/video" 

# Ensure directory exists within the volume
if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR, exist_ok=True)

# --- PUBLIC URL ---
# 🟢 UPDATE THIS URL DAILY (Ya Railway ka public domain yahan daalein)
BASE_PUBLIC_URL = "https://snakiest-edward-autochthonously.ngrok-free.dev"

# --- API KEYS & SECRETS ---
# Railway ke 'Variables' tab mein in sab ka hona lazmi hai
SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY") # Isay uncomment kar diya hai
SHOPIFY_API_SECRET = os.getenv("SHOPIFY_API_SECRET")
META_CLIENT_ID = os.getenv("META_CLIENT_ID")
META_CLIENT_SECRET = os.getenv("META_CLIENT_SECRET")
IG_USER_ID = os.getenv("IG_USER_ID")
TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
