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

            videos = []
            for entry in results.get("entries", []):
                videos.append({
                    "title": entry.get("title"),
                    "video_id": entry.get("id")
                })

            return videos

    except Exception as e:
        return {"error": str(e)}


# 🎧 AUDIO API (FINAL WORKING)
@app.get("/audio")
def get_audio(video_id: str):
    url = f"https://youtu.be/{video_id}"

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "cookiefile": "cookies.txt"   # 🔥 important
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # ✅ direct playable URL
            audio_url = info.get("url")

            if not audio_url:
                return {"error": "Audio URL not found"}

            return {
                "title": info.get("title"),
                "audio_url": audio_url
            }

    except Exception as e:
        return {"error": str(e)}
