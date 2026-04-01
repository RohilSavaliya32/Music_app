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

def get_video_info(video_url):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
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
        return ydl.extract_info(video_url, download=False)


@app.get("/search")
def search(q: str):
    try:
        # 🔥 STEP 1: ONLY SEARCH (NO FORMAT ISSUE)
        with yt_dlp.YoutubeDL({
            "quiet": True,
            "extract_flat": True
        }) as ydl:

            print(f"🔍 Searching: {q}")
            results = ydl.extract_info(f"ytsearch1:{q}", download=False)

        entries = results.get("entries", [])

        if not entries:
            return {"error": "No result found"}

        video_id = entries[0].get("id")
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        print(f"🎯 Selected Video ID: {video_id}")

        # 🔥 STEP 2: FETCH FULL DATA (SAFE)
        info = get_video_info(video_url)

        # 🎧 BEST AUDIO PICK
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
