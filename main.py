from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import time
import random

app = FastAPI()

# ✅ CORS (Flutter ke liye)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ In-memory cache
cache = {}

# ✅ yt-dlp config
def get_ydl_opts():
    return {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "cookiesfrombrowser": ("chrome", None),  # 🔥 auto cookies
    }


# 🏠 Home
@app.get("/")
def home():
    return {"msg": "Music API Running 🚀"}


# 🎵 Get Song
@app.get("/song")
def get_song(url: str):
    
    # ✅ Cache check
    if url in cache:
        return {
            "source": "cache",
            "data": cache[url]
        }

    # ⏱ Random delay (bot avoid)
    time.sleep(random.uniform(1, 2))

    # 🔁 Retry system
    for attempt in range(3):
        try:
            with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
                info = ydl.extract_info(url, download=False)

            result = {
                "title": info.get("title"),
                "duration": info.get("duration"),
                "thumbnail": info.get("thumbnail"),
                "audio_url": info.get("url"),
            }

            # ✅ Cache store
            cache[url] = result

            return {
                "source": "yt-dlp",
                "data": result
            }

        except Exception as e:
            print(f"Retry {attempt+1} failed:", str(e))
            time.sleep(2)

    return {"error": "Failed to fetch audio 😢"}


# 🔍 Search (optional)
@app.get("/search")
def search(q: str):
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(f"ytsearch10:{q}", download=False)

        videos = []
        for entry in results.get("entries", []):
            videos.append({
                "title": entry.get("title"),
                "id": entry.get("id"),
                "url": f"https://www.youtube.com/watch?v={entry.get('id')}",
                "thumbnail": entry.get("thumbnail"),
            })

        return {"results": videos}

    except Exception as e:
        return {"error": str(e)}
