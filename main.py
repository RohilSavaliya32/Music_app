from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI()

# ✅ CORS (Flutter ke liye)
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
        "format": "bestaudio/best",

        # 🔥 BOT BYPASS SETTINGS
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

            # 🔥 Try 1: normal search
            try:
                print(f"🔍 Searching: {q}")
                results = ydl.extract_info(f"ytsearch1:{q}", download=False)
            except Exception as e:
                print("⚠️ First search failed, trying fallback...")
                # 🔁 fallback
                results = ydl.extract_info(f"ytsearch1:{q} official audio", download=False)

        entries = results.get("entries", [])

        if not entries:
            return {"error": "No result found"}

        entry = entries[0]

        print(f"✅ Found: {entry.get('title')}")

        # 🎧 Audio URL extract
        audio_url = entry.get("url")

        if not audio_url:
            print("⚠️ Direct URL not found, checking formats...")
            for f in entry.get("formats", []):
                if f.get("acodec") != "none" and f.get("url"):
                    audio_url = f.get("url")
                    break

        if not audio_url:
            return {"error": "Audio not found"}

        youtube_url = f"https://youtu.be/{entry.get('id')}"

        return {
            "title": entry.get("title"),
            "video_id": entry.get("id"),
            "thumbnail": entry.get("thumbnail"),
            "channel": entry.get("uploader"),
            "duration": entry.get("duration"),
            "views": entry.get("view_count"),
            "youtube_url": youtube_url,
            "audio_url": audio_url
        }

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"error": f"Failed: {str(e)}"}
