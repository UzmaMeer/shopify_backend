import os
import requests
import uuid
import subprocess
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont, ImageColor, ImageFilter
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import platform 
import asyncio
import pyttsx3 
import re
import textwrap 
from motor.motor_asyncio import AsyncIOMotorClient

# 1. Import Shared Path from config to ensure volume (/app/video) is used
#
from config import VIDEO_DIR

# Disable SSL Warnings for external requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
WIDTH, HEIGHT = 480, 854 
BGM_URL = "https://www.bensound.com/bensound-music/bensound-elevate.mp3" 

# 2. Gemini Setup using Environment Variable for security
#
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_KEY)

# 3. Database Connection using Railway environment variables
#
MONGO_DETAILS = os.getenv("MONGO_DETAILS", "mongodb://localhost:27017")
client_db = AsyncIOMotorClient(MONGO_DETAILS)
db = client_db.video_ai_db
brand_collection = db.get_collection("brand_settings")

def get_ffmpeg_codec():
    """Detects available FFmpeg codecs based on the operating system."""
    system = platform.system()
    try:
        subprocess.run(['ffmpeg', '-hide_banner', '-encoders'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if system == "Darwin": return "h264_videotoolbox"
        return "libx264" 
    except:
        return "libx264"

VIDEO_CODEC = get_ffmpeg_codec()

def get_audio_duration(file_path):
    """Retrieves the duration of an audio file using ffprobe."""
    if not file_path or not os.path.exists(file_path): return 15.0
    try:
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', file_path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return float(result.stdout.strip())
    except: return 15.0

# ⚡ TASK A: AUDIO CHAIN
def process_audio_chain(title, desc, gender, script_tone, duration):
    """Generates a script via AI and converts it to speech using pyttsx3."""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        clean_desc = desc.replace('<p>', '').replace('</p>', '').replace('<br>', ' ')
        target_word_count = int(float(duration) * 2.2) 
        
        prompt = (
            f"Write a spoken video script for product: '{title}'.\n"
            f"Description: '{clean_desc}'\n"
            f"Tone: {script_tone}. Duration: {duration}s (~{target_word_count} words).\n"
            f"Just text. No scene descriptions."
        )
        
        print(f"🤖 [AI] Generating Script...")
        response = model.generate_content(prompt)
        clean_script = re.sub(r"(\*\*|Script:|\[.*?\]|\"|Voiceover:)", "", response.text, flags=re.IGNORECASE).strip()

        vo_filename = f"vo_{uuid.uuid4().hex[:8]}.mp3"
        vo_path = os.path.join(VIDEO_DIR, vo_filename)
        
        engine = pyttsx3.init()
        engine.setProperty('rate', 145) 
        
        voices = engine.getProperty('voices')
        target_voice = None
        for voice in voices:
            v_name = voice.name.lower()
            if gender == "female" and ("zira" in v_name or "female" in v_name): target_voice = voice.id; break
            elif gender == "male" and ("david" in v_name or "male" in v_name): target_voice = voice.id; break
        
        if target_voice: engine.setProperty('voice', target_voice)
        engine.save_to_file(clean_script, vo_path)
        engine.runAndWait()
        
        if not os.path.exists(vo_path) or os.path.getsize(vo_path) == 0:
            return None, clean_script

        return vo_path, clean_script

    except Exception as e:
        print(f"❌ Audio Chain Error: {e}")
        return None, ""

# ⚡ TASK B: IMAGE PROCESSING
def create_robust_session():
    """Creates a requests session with retry logic for stable image downloads."""
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    return session

def download_and_process_image(args):
    """Downloads an image, validates it, and resizes it for the video resolution."""
    i, url, is_audio, is_logo, session = args 
    try:
        res = session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20, verify=False)
        if res.status_code == 200:
            content_type = res.headers.get("Content-Type", "")
            if "text/html" in content_type:
                return None

            ext = 'mp3' if is_audio else 'png' if is_logo else 'jpg'
            name = os.path.join(VIDEO_DIR, f"temp_{uuid.uuid4().hex[:8]}.{ext}")
            with open(name, 'wb') as f: f.write(res.content)
            
            if not is_audio:
                try:
                    with Image.open(name) as img:
                        img.verify() 
                except Exception:
                    if os.path.exists(name): os.remove(name)
                    return None

            # Resize to mobile vertical resolution
            if not is_audio and not is_logo:
                try:
                    with Image.open(name) as img:
                        img = img.convert("RGB")
                        img_ratio = img.width / img.height
                        target_ratio = WIDTH / HEIGHT

                        if img_ratio > target_ratio:
                            new_w = WIDTH
                            new_h = int(WIDTH / img_ratio)
                        else:
                            new_h = HEIGHT
                            new_w = int(HEIGHT * img_ratio)

                        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

                        final_canvas = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
                        final_canvas.paste(img, ((WIDTH - new_w) // 2, (HEIGHT - new_h) // 2))
                        final_canvas.save(name, "JPEG", quality=95)
                except: pass
            
            if is_logo:
                try:
                    with Image.open(name) as img:
                        img.thumbnail((150, 150)); img.save(name, "PNG")
                except: pass
            return (i, name)
    except: return None

def create_template_overlay(template_id, output_path):
    """Creates a graphical overlay based on selected video themes (Sale, Luxury, etc.)."""
    if not template_id or str(template_id).lower() in ["none", "null", ""]: return None
    
    try:
        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
        draw = ImageDraw.Draw(overlay)
        try: font = ImageFont.truetype("arial.ttf", 50)
        except: font = ImageFont.load_default()

        color_map = { "sale": "#e11d48", "winter": "#0891b2", "luxury": "#d4af37", "kids": "#ff5733" }
        text_map = { "sale": "FLASH SALE", "winter": "WINTER SPECIAL", "luxury": "PREMIUM", "kids": "KIDS ZONE" }

        color = color_map.get(template_id, "#000000")
        text = text_map.get(template_id, "")

        draw.rectangle([0, 0, WIDTH, HEIGHT], outline=color, width=20)
        draw.rectangle([0, 0, WIDTH, 80], fill=color)
        draw.text((WIDTH//2, 40), text, font=font, fill="white", anchor="mm")
        draw.rectangle([0, HEIGHT-60, WIDTH, HEIGHT], fill=color)

        overlay.save(output_path, "PNG")
        return output_path
    except: return None

def create_outro_image(last_image_path, text, output_path, cta_text="ORDER NOW", brand_color="#FFD700"):
    """Creates a final call-to-action slide for the end of the video."""
    try:
        if last_image_path and os.path.exists(last_image_path):
            base = Image.open(last_image_path).convert("RGB").filter(ImageFilter.GaussianBlur(15))
        else:
            base = Image.new("RGB", (WIDTH, HEIGHT), (20, 20, 20))

        base = base.resize((WIDTH, HEIGHT))
        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 150))
        base.paste(overlay, (0, 0), overlay)
        draw = ImageDraw.Draw(base)
        
        try: font = ImageFont.truetype("arial.ttf", 36)
        except: font = ImageFont.load_default()

        lines = textwrap.wrap(text, width=25)
        y = HEIGHT // 2 - (len(lines) * 20)
        for line in lines:
            draw.text((WIDTH//2, y), line, font=font, fill="white", anchor="mm")
            y += 40
        
        draw.text((WIDTH//2, y+40), cta_text, font=font, fill=brand_color, anchor="mm")
        base.save(output_path)
        return output_path
    except: return None

async def fetch_brand_settings(shop_name):
    """Retrieves stored brand kit settings (colors, logo) from the database."""
    if not shop_name: return None
    try: return await brand_collection.find_one({"shop": shop_name})
    except: return None

# 🚀 MAIN FUNCTION: Handles the entire video assembly process
def generate_video_from_images(image_urls, product_title, product_desc, logo_url=None, gender="female", 
                               target_duration=15, script_tone="Professional", custom_music_path=None, 
                               progress_callback=None, shop_name=None, video_theme="Modern", 
                               bgm_file_path=None, template_id="none"):
    
    if not os.path.exists(VIDEO_DIR): os.makedirs(VIDEO_DIR)
    if progress_callback: progress_callback(5)

    # 1. Fetch Brand Kit data
    brand_color, cta_text = "#FFD700", "ORDER NOW"
    if shop_name:
        try:
            settings = asyncio.run(fetch_brand_settings(shop_name))
            if settings:
                if settings.get("primary_color"): brand_color = settings["primary_color"]
                if settings.get("cta_text"): cta_text = settings["cta_text"]
                if settings.get("logo_url") and not logo_url: logo_url = settings["logo_url"]
        except: pass

    downloaded_images, bgm_file, vo_file, logo_file, script_text = [], None, None, None, ""

    if custom_music_path and os.path.exists(custom_music_path):
        bgm_file = custom_music_path

    # Parallel Download of all media assets
    session = create_robust_session()
    with ThreadPoolExecutor(max_workers=8) as exec:
        future_audio = exec.submit(process_audio_chain, product_title, product_desc, gender, script_tone, target_duration)
        tasks = [(i, url, False, False, session) for i, url in enumerate(image_urls)]
        if not bgm_file: tasks.append((99, BGM_URL, True, False, session))
        if logo_url: tasks.append((100, logo_url, False, True, session))
        
        for future in as_completed([exec.submit(download_and_process_image, t) for t in tasks]):
            res = future.result()
            if res:
                if res[0] == 99: bgm_file = res[1]
                elif res[0] == 100: logo_file = res[1]
                else: downloaded_images.append(res)
        vo_file, script_text = future_audio.result()
    session.close()

    if not downloaded_images: return None, "No Images"
    downloaded_images.sort()

    try:
        # Assemble Extras: Outro and Theme Overlays
        last_img = downloaded_images[-1][1]
        outro_path = os.path.join(VIDEO_DIR, f"outro_{uuid.uuid4().hex[:6]}.jpg")
        create_outro_image(last_img, product_title, outro_path, cta_text=cta_text, brand_color=brand_color)
        if os.path.exists(outro_path): downloaded_images.append((999, outro_path))

        overlay_path = os.path.join(VIDEO_DIR, f"overlay_{uuid.uuid4().hex[:6]}.png")
        generated_overlay = create_template_overlay(template_id, overlay_path)

        # Calculate final video and image slide durations
        audio_dur = get_audio_duration(vo_file) if vo_file else 0
        final_dur = max(5.0, min(float(target_duration), audio_dur if audio_dur > 0 else float(target_duration)))
        num_images = len(downloaded_images)
        img_dur = (final_dur - 3.0) / max(1, num_images - 1)

        output_name = f"vid_{uuid.uuid4().hex[:6]}.mp4"
        output_path = os.path.join(VIDEO_DIR, output_name)
        
        # Assemble FFmpeg filter complex for uniform scaling
        input_args, filter_complex, concat_v, current_idx = [], "", "", 0
        
        for i, item in enumerate(downloaded_images):
            input_args.extend(["-loop", "1", "-t", str(3.0 if i==num_images-1 else img_dur), "-i", item[1]])
            filter_complex += f"[{current_idx}:v]scale=480:854,setsar=1[v{current_idx}];"
            concat_v += f"[v{current_idx}]"
            current_idx += 1
        
        filter_complex += f"{concat_v}concat=n={num_images}:v=1:a=0[base];"
        last_node = "[base]"

        # Add graphical overlays if enabled
        if generated_overlay and os.path.exists(generated_overlay):
            input_args.extend(["-loop", "1", "-i", generated_overlay])
            filter_complex += f"{last_node}[{current_idx}:v]overlay=0:0[v_over];"
            last_node = "[v_over]"
            current_idx += 1

        # Add branding logo to the corner
        if logo_file and os.path.exists(logo_file):
            input_args.extend(["-i", logo_file])
            filter_complex += f"{last_node}[{current_idx}:v]overlay=W-w-20:40[v_final];"
            last_node = "[v_final]"
            current_idx += 1

        # Audio mixing: combine background music and voiceover
        bgm_in = bgm_file if (bgm_file and os.path.exists(bgm_file)) else "anullsrc"
        input_args.extend(["-stream_loop", "-1", "-i", bgm_in])
        bgm_idx = current_idx
        current_idx += 1
        
        audio_map = ""
        if vo_file and os.path.exists(vo_file):
            input_args.extend(["-i", vo_file])
            vo_idx = current_idx
            filter_complex += f"[{bgm_idx}:a]volume=0.2[bg];[{vo_idx}:a]volume=2.0[vo];[bg][vo]amix=inputs=2:duration=first[a_out]"
            audio_map = "[a_out]"
        else:
            filter_complex += f"[{bgm_idx}:a]volume=0.5[a_out]"
            audio_map = "[a_out]"

        # Construct final FFmpeg command for rendering
        cmd = [
            'ffmpeg', '-y', *input_args, 
            '-filter_complex', filter_complex, 
            '-map', last_node, '-map', audio_map, 
            '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'zerolatency', 
            '-pix_fmt', 'yuv420p', '-shortest', output_path
        ]
        
        if progress_callback: progress_callback(70)
        subprocess.run(cmd, check=True) 
        
        if progress_callback: progress_callback(100)
        return output_name, script_text

    except Exception as e:
        print(f"❌ Error during video generation: {e}")
        return None, ""
    finally:
        # Cleanup temporary files from the shared volume to save space
        for _, f in downloaded_images: 
            if os.path.exists(f): os.remove(f)
        if vo_file and os.path.exists(vo_file): os.remove(vo_file)
        if bgm_file and os.path.exists(bgm_file) and "bensound" in BGM_URL: os.remove(bgm_file)
        if logo_file and os.path.exists(logo_file): os.remove(logo_file)
        if 'generated_overlay' in locals() and generated_overlay and os.path.exists(generated_overlay): 
            os.remove(generated_overlay)
