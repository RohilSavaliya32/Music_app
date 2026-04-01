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
    try:
        # 🔥 STEP 1: SEARCH ONLY (NO FORMAT LOAD)
        with yt_dlp.YoutubeDL({
            "quiet": True,
            "extract_flat": "in_playlist"
        }) as ydl:

            print(f"🔍 Searching: {q}")
            results = ydl.extract_info(f"ytsearch1:{q}", download=False)

        entries = results.get("entries", [])

        if not entries:
            return {"error": "No result found"}

        video_id = entries[0].get("id")
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        print(f"🎯 Video ID: {video_id}")

        # 🔥 STEP 2: GET ONLY METADATA (NO FORMAT ERROR)
        ydl_opts = {
            "quiet": True,
            "skip_download": True,   # 🔥 key fix
            "extract_flat": False,

            "cookiefile": "cookies.txt",
            "nocheckcertificate": True,
            "geo_bypass": True,

            "headers": {
                "User-Agent": "Mozilla/5.0"
            },

            "extractor_args": {
                "youtube": {
                    "player_client": ["android"]
                }
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

        # 🎧 AUDIO PICK (SAFE)
        formats = info.get("formats", [])

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
            "title": info.get("title"),
            "video_id": video_id,
            "thumbnail": info.get("thumbnail"),
            "channel": info.get("uploader"),
            "youtube_url": f"https://youtu.be/{video_id}",
            "audio_url": audio_url
        }

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"error": f"Failed: {str(e)}"}
