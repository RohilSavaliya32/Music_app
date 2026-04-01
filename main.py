from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI()

# CORS (Flutter ke liye)
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
        "format": "bestaudio/best"
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(f"ytsearch1:{q} song", download=False)

        entries = results.get("entries", [])

        if not entries:
            return {"error": "No result found"}

        entry = entries[0]

        audio_url = entry.get("url")

        if not audio_url:
            for f in entry.get("formats", []):
                if f.get("acodec") != "none" and f.get("url"):
                    audio_url = f.get("url")
                    break

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
        return {"error": str(e)}
