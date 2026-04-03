from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import time

app = FastAPI()

rooms = {}
hosts = {}
room_state = {}  # 🧠 store current video state


@app.get("/")
def home():
    return {"status": "running"}


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()

    # 🆕 create room
    if room_id not in rooms:
        rooms[room_id] = []
        hosts[room_id] = websocket
        room_state[room_id] = {
            "time": 0,
            "isPlaying": False
        }

    rooms[room_id].append(websocket)

    # 👑 send role
    role = "host" if websocket == hosts[room_id] else "viewer"
    await websocket.send_json({
        "type": "role",
        "role": role
    })

    # 🔄 SEND CURRENT STATE TO NEW USER
    try:
        await websocket.send_json({
            "type": "sync",
            "time": room_state[room_id]["time"],
            "isPlaying": room_state[room_id]["isPlaying"],
            "server_time": int(time.time() * 1000)
        })
    except:
        pass

    try:
        while True:
            data = await websocket.receive_json()

            # 🧠 ADD SERVER TIMESTAMP
            data["server_time"] = int(time.time() * 1000)

            # 👑 only host controls
            if websocket == hosts[room_id]:

                # 🧠 UPDATE ROOM STATE
                if data.get("action") in ["play", "pause", "seek", "sync"]:
                    room_state[room_id]["time"] = data.get("time", 0)

                    if data.get("action") == "play":
                        room_state[room_id]["isPlaying"] = True
                    elif data.get("action") == "pause":
                        room_state[room_id]["isPlaying"] = False

                dead_connections = []

                # 📡 broadcast
                for connection in rooms[room_id]:
                    if connection != websocket:
                        try:
                            await connection.send_json(data)
                        except:
                            dead_connections.append(connection)

                # 🧹 cleanup dead
                for dc in dead_connections:
                    if dc in rooms[room_id]:
                        rooms[room_id].remove(dc)

    except WebSocketDisconnect:
        if room_id in rooms and websocket in rooms[room_id]:
            rooms[room_id].remove(websocket)

        # 👑 host leave logic
        if room_id in hosts and websocket == hosts[room_id]:
            if rooms[room_id]:
                new_host = rooms[room_id][0]
                hosts[room_id] = new_host

                # notify new host
                try:
                    await new_host.send_json({
                        "type": "role",
                        "role": "host"
                    })
                except:
                    pass
            else:
                # 🧹 delete room completely
                del rooms[room_id]
                del hosts[room_id]
                del room_state[room_id]
