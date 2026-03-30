from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import yt_dlp

app = FastAPI()

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 SIMPLE CACHE (memory)
audio_cache = {}

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

        # ✅ FILTER ONLY VALID VIDEOS
        videos = [
            {
                "title": entry.get("title"),
                "video_id": entry.get("id"),
                "thumbnail": entry.get("thumbnails", [{}])[-1].get("url")
            }
            for entry in results.get("entries", [])
            if entry.get("id") and len(entry.get("id")) == 11
        ]

        return videos

    except Exception as e:
        return {"error": str(e)}


# 🎧 AUDIO API
@app.get("/audio")
def get_audio(video_id: str):

    # 🔥 CACHE CHECK
    if video_id in audio_cache:
        return audio_cache[video_id]

    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "geo_bypass": True,

        # ✅ SIMPLE FORMAT
        "format": "bestaudio/best",

        # 🔥 MULTI CLIENT TRY
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios", "web"]
            }
        },

        # 🔥 HEADERS
        "http_headers": {
            "User-Agent": "Mozilla/5.0"
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        audio_url = info.get("url")

        # 🔥 FALLBACK (formats)
        if not audio_url:
            formats = info.get("formats", [])

            audio_formats = [
                f for f in formats
                if f.get("acodec") != "none" and f.get("url")
            ]

            audio_formats.sort(key=lambda x: x.get("abr", 0), reverse=True)

            if audio_formats:
                audio_url = audio_formats[0]["url"]

        # ❌ STILL FAIL
        if not audio_url:
            return JSONResponse(
                {"error": "No audio found"},
                status_code=404
            )

        response = {
            "title": info.get("title"),
            "audio_url": audio_url,
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail")
        }

        # 🔥 SAVE TO CACHE
        audio_cache[video_id] = response

        return response

    except Exception as e:
        error_msg = str(e)

        # 🔥 HANDLE YOUTUBE BLOCK
        if "Sign in to confirm you're not a bot" in error_msg:
            return JSONResponse(
                {
                    "error": "YouTube blocked request",
                    "solution": "Use local/ngrok backend"
                },
                status_code=500
            )

        return JSONResponse(
            {"error": error_msg},
            status_code=500
        )
