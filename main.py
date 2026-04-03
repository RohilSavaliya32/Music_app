from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

rooms = {}
hosts = {}

@app.get("/")
def home():
    return {"status": "running"}

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()

    # create room
    if room_id not in rooms:
        rooms[room_id] = []
        hosts[room_id] = websocket

    rooms[room_id].append(websocket)

    # send role
    role = "host" if websocket == hosts[room_id] else "viewer"
    await websocket.send_json({
        "type": "role",
        "role": role
    })

    try:
        while True:
            data = await websocket.receive_json()

            # only host controls
            if websocket == hosts[room_id]:
                dead_connections = []

                for connection in rooms[room_id]:
                    if connection != websocket:
                        try:
                            await connection.send_json(data)
                        except:
                            dead_connections.append(connection)

                # remove dead sockets
                for dc in dead_connections:
                    if dc in rooms[room_id]:
                        rooms[room_id].remove(dc)

    except WebSocketDisconnect:
        if room_id in rooms and websocket in rooms[room_id]:
            rooms[room_id].remove(websocket)

        # host leave logic
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
                # delete room
                del rooms[room_id]
                del hosts[room_id]
