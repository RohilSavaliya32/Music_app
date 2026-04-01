from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/search")
def search(q: str):
    ydl_opts = {
        "quiet": True,
        "noplaylist": True,

        # 🔥 MOST IMPORTANT FIX
        "skip_download": True,

        # ✅ cookies
        "cookiefile": "cookies.txt",

        "nocheckcertificate": True,
        "geo_bypass": True,

        "headers": {
            "User-Agent": "Mozilla/5.0"
        },

        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web", "tv"]
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            print(f"🔍 Searching: {q}")

            try:
                results = ydl.extract_info(f"ytsearch1:{q}", download=False)
            except:
                print("⚠️ fallback search...")
                results = ydl.extract_info(f"ytsearch1:{q} official audio", download=False)

        entries = results.get("entries", [])

        if not entries:
            return {"error": "No result found"}

        entry = entries[0]

        print(f"✅ Found: {entry.get('title')}")

        # 🎧 SAFE AUDIO PICKER
        formats = entry.get("formats", [])

        best_audio = None
        best_bitrate = 0

        for f in formats:
            if f.get("acodec") != "none" and f.get("url"):
                abr = f.get("abr") or 0
                if abr > best_bitrate:
                    best_bitrate = abr
                    best_audio = f

        if not best_audio:
            return {"error": "No audio format found"}

        audio_url = best_audio.get("url")

        return {
            "title": entry.get("title"),
            "video_id": entry.get("id"),
            "thumbnail": entry.get("thumbnail"),
            "channel": entry.get("uploader"),
            "youtube_url": f"https://youtu.be/{entry.get('id')}",
            "audio_url": audio_url
        }

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"error": f"Failed: {str(e)}"}
