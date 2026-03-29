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

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        results = ydl.extract_info(f"ytsearch5:{q}", download=False)

        videos = []
        for entry in results['entries']:
            videos.append({
                "title": entry.get("title"),
                "video_id": entry.get("id")
            })

        return videos


# 🎧 AUDIO API
@app.get("/audio")
def get_audio(video_id: str):
    url = f"https://youtu.be/{video_id}"

    ydl_opts = {
        "format": "bestaudio",
        "quiet": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        return {
            "title": info.get("title"),
            "audio_url": info.get("url")
        }