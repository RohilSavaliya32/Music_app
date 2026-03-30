from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import requests

app = FastAPI()

# ✅ CORS
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
            results = ydl.extract_info(f"ytsearch5:{q}", download=False)

        videos = [
            {
                "title": entry.get("title"),
                "video_id": entry.get("id")
            }
            for entry in results.get("entries", [])
        ]

        return videos

    except Exception as e:
        return {"error": str(e)}


# 🎧 AUDIO API
@app.get("/audio")
def get_audio(video_id: str):
    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "geo_bypass": True,
        "socket_timeout": 30,

        # 🔥 FIXED CLIENT BYPASS
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios", "web_embedded", "tv"]
            }
        },

        # ✅ SIMPLE FORMAT (NO CRASH)
        "format": "bestaudio/best",

        # 🔥 STRONG HEADERS
        "http_headers": {
            "User-Agent": "com.google.android.youtube/17.31.35 (Linux; Android 11)",
        }
    }

    try:
        # 🔍 Extract info
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        audio_url = info.get("url")

        # 🔥 FALLBACK (IMPORTANT)
        if not audio_url:
            formats = info.get("formats", [])

            audio_formats = [
                f for f in formats
                if f.get("acodec") != "none" and f.get("url")
            ]

            # Sort by best quality
            audio_formats.sort(key=lambda x: x.get("abr", 0), reverse=True)

            if audio_formats:
                audio_url = audio_formats[0]["url"]

        # ❌ Still not found
        if not audio_url:
            return JSONResponse(
                {"error": "No playable audio found"},
                status_code=404
            )

        # 🚀 STREAM TRY
        try:
            response = requests.get(
                audio_url,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Referer": "https://www.youtube.com/"
                },
                stream=True,
                timeout=20
            )

            response.raise_for_status()

            return StreamingResponse(
                response.iter_content(chunk_size=8192),
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": f"inline; filename={info.get('title','audio')}.mp3",
                    "Accept-Ranges": "bytes"
                }
            )

        except Exception:
            # 🔥 BEST FALLBACK → RETURN DIRECT URL
            return {
                "title": info.get("title"),
                "audio_url": audio_url,
                "duration": info.get("duration"),
                "note": "Play this URL directly in frontend"
            }

    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to fetch audio: {str(e)}"},
            status_code=500
        )
