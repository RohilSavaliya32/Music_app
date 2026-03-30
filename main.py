from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import yt_dlp

app = FastAPI()

# ✅ CORS (Flutter connect ke liye)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔍 SEARCH API
@app.get("/search")
def search(q: str):
    ydl_opts = {
        "quiet": True,
        "extract_flat": True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(f"ytsearch10:{q}", download=False)

        videos = [
            {
                "title": entry.get("title"),
                "video_id": entry.get("id"),
                "thumbnail": entry.get("thumbnails", [{}])[-1].get("url")
            }
            for entry in results.get("entries", [])
        ]

        return videos

    except Exception as e:
        return {"error": str(e)}


# 🎧 AUDIO URL API (BEST METHOD)
@app.get("/audio")
def get_audio(video_id: str):
    url = f"https://www.youtube.com/watch?v={video_id}"

    # 🔥 Strong yt-dlp config
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "geo_bypass": True,

        # ✅ BEST FORMAT
        "format": "bestaudio/best",

        # 🔥 YouTube bypass clients
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios", "web_embedded"]
            }
        },

        # 🔥 Headers
        "http_headers": {
            "User-Agent": "com.google.android.youtube/17.31.35"
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        # 🎯 Direct audio URL
        audio_url = info.get("url")

        # 🔥 fallback if missing
        if not audio_url:
            formats = info.get("formats", [])

            audio_formats = [
                f for f in formats
                if f.get("acodec") != "none" and f.get("url")
            ]

            audio_formats.sort(key=lambda x: x.get("abr", 0), reverse=True)

            if audio_formats:
                audio_url = audio_formats[0]["url"]

        if not audio_url:
            return JSONResponse(
                {"error": "No audio found"},
                status_code=404
            )

        return {
            "title": info.get("title"),
            "audio_url": audio_url,
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail")
        }

    except Exception as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )   
