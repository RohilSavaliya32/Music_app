from fastapi import FastAPI
import yt_dlp

app = FastAPI()

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


# 🎧 AUDIO API (FINAL FIXED)
@app.get("/audio")
def get_audio(video_id: str):
    url = f"https://youtu.be/{video_id}"

    # ✅ CORRECT INDENT
    ydl_opts = {
        "quiet": True,
        "noplaylist": True,
        "cookiefile": "cookies.txt",
        "nocheckcertificate": True,
        "geo_bypass": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"]
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        formats = info.get("formats", [])

        audio_url = None

        # ✅ Best audio-only stream
        for f in formats:
            if f.get("acodec") != "none" and f.get("vcodec") == "none":
                audio_url = f.get("url")
                break

        # 🔁 fallback
        if not audio_url:
            for f in formats:
                if f.get("url"):
                    audio_url = f.get("url")
                    break

        if not audio_url:
            return {"error": "No playable audio found"}

        return {
            "title": info.get("title"),
            "audio_url": audio_url
        }

    except Exception as e:
        return {"error": str(e)}
