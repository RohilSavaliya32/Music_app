from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"msg": "Rohil Backend live ho gya 🚀"}

@app.get("/song")
def get_song():
    return {
        "title": "Test Song",
        "url": "https://example.com/song.mp3"
    }   