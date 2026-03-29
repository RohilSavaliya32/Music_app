from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import requests
from io import BytesIO

app = FastAPI()

# ✅ Enable CORS for Flutter app
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


# 🎧 AUDIO API - Stream directly
@app.get("/audio")
def get_audio(video_id: str):
    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "cookiefile": "cookies.txt",
        "nocheckcertificate": True,
        "geo_bypass": True,
        "socket_timeout": 30,
        "format": "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best[acodec!=none]/best",
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web", "tv", "mweb", "ios"]
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        # Get audio URL
        audio_url = info.get("url")
        
        if not audio_url:
            formats = info.get("formats", [])
            # Try to find best audio format
            for f in formats:
                if f.get("acodec") != "none" and f.get("url"):
                    audio_url = f.get("url")
                    break

        if not audio_url:
            return JSONResponse(
                {"error": "No audio format available for this video"},
                status_code=404
            )

        # Stream audio from YouTube
        try:
            response = requests.get(
                audio_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://www.youtube.com/"
                },
                stream=True,
                timeout=30
            )
            response.raise_for_status()

            return StreamingResponse(
                response.iter_content(chunk_size=8192),
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": f"inline; filename={info.get('title', 'audio')}.mp3",
                    "Accept-Ranges": "bytes",
                    "Cache-Control": "no-cache"
                }
            )
        except Exception as stream_error:
            # Fallback: Return URL if streaming fails
            return JSONResponse({
                "title": info.get("title"),
                "audio_url": audio_url,
                "duration": info.get("duration"),
                "note": "Use URL directly if streaming fails"
            })

    except Exception as e:
        error_msg = str(e)
        # Return more specific error handling
        return JSONResponse(
            {"error": f"Failed to fetch audio: {error_msg}"},
            status_code=500
        )
