from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

# room storage
rooms = {}
hosts = {}

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()

    # create room if not exists
    if room_id not in rooms:
        rooms[room_id] = []
        hosts[room_id] = websocket  # first user = host

    rooms[room_id].append(websocket)

    # send role
    if websocket == hosts[room_id]:
        await websocket.send_json({
            "type": "role",
            "role": "host"
        })
    else:
        await websocket.send_json({
            "type": "role",
            "role": "viewer"
        })

    try:
        while True:
            data = await websocket.receive_json()

            # only host can send control events
            if websocket == hosts[room_id]:
                for connection in rooms[room_id]:
                    if connection != websocket:
                        await connection.send_json(data)

    except WebSocketDisconnect:
        rooms[room_id].remove(websocket)

        # if host leaves → assign new host
        if websocket == hosts[room_id]:
            if rooms[room_id]:
                hosts[room_id] = rooms[room_id][0]
            else:
                del rooms[room_id]
                del hosts[room_id]
