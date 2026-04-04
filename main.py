from time import time
from typing import Any
from uuid import uuid4
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

DEFAULT_MEDIA_URL = "https://www.w3schools.com/html/mov_bbb.mp4"
rooms: dict[str, dict[str, Any]] = {}

def now_ms() -> int:
    return int(time() * 1000)

def build_room(room_id: str, password: str | None, host_name: str) -> dict[str, Any]:
    return {
        "id": room_id,
        "password": password or "",
        "participants": {},
        "host_id": None,
        "co_hosts": set(),
        "messages": [],
        "pinned_message_id": None,
        "kicked_users": [],
        "media": {
            "url": DEFAULT_MEDIA_URL,
            "type": "video",
            "title": "Demo video",
            "audioOnly": False,
        },
        "playback": {
            "position_ms": 0,
            "is_playing": False,
            "updated_at": now_ms(),
            "latency_hint_ms": 0,
            "buffering": False,
        },
    }

def role_for(room: dict[str, Any], client_id: str) -> str:
    if room["host_id"] == client_id:
        return "host"
    if client_id in room["co_hosts"]:
        return "co-host"
    return "viewer"

def participant_payload(room: dict[str, Any]) -> list[dict[str, Any]]:
    return [{"id": cid, "username": p["username"], "role": role_for(room, cid)} 
            for cid, p in room["participants"].items()]

async def broadcast(room: dict[str, Any], payload: dict[str, Any], exclude: str | None = None):
    dead = []
    for cid, p in room["participants"].items():
        if exclude and cid == exclude:
            continue
        try:
            await p["socket"].send_json(payload)
        except:
            dead.append(cid)
    for cid in dead:
        room["participants"].pop(cid, None)

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    username = (websocket.query_params.get("username") or "Guest").strip()[:24]
    password = (websocket.query_params.get("password") or "").strip()
    
    await websocket.accept()
    
    room = rooms.get(room_id)
    if not room:
        room = build_room(room_id, password or None, username)
        rooms[room_id] = room
    elif room["password"] and room["password"] != password:
        await websocket.send_json({"type": "error", "message": "Wrong password"})
        await websocket.close()
        return
    
    client_id = str(uuid4())
    room["participants"][client_id] = {"id": client_id, "username": username, "socket": websocket}
    
    if not room["host_id"]:
        room["host_id"] = client_id
    
    await websocket.send_json({
        "type": "welcome",
        "clientId": client_id,
        "role": role_for(room, client_id),
        "room": {
            "id": room["id"],
            "hostId": room["host_id"],
            "participants": participant_payload(room),
            "messages": room["messages"][-50:],
            "pinnedMessageId": room["pinned_message_id"],
            "media": room["media"],
            "playback": {"position": room["playback"]["position_ms"], "isPlaying": room["playback"]["is_playing"]}
        }
    })
    
    await broadcast(room, {"type": "participants", "participants": participant_payload(room), "hostId": room["host_id"]})
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "chat":
                msg = {"id": str(uuid4()), "userId": client_id, "username": username, "text": data.get("text", "")[:400], "timestamp": now_ms()}
                room["messages"].append(msg)
                await broadcast(room, {"type": "chat", "message": msg})
            
            elif msg_type == "pin_message" and room["host_id"] == client_id:
                room["pinned_message_id"] = data.get("messageId")
                await broadcast(room, {"type": "pin_message", "messageId": room["pinned_message_id"]})
            
            elif msg_type == "media_update" and role_for(room, client_id) in ["host", "co-host"]:
                room["media"] = {"url": data.get("url", DEFAULT_MEDIA_URL), "title": data.get("title", "Media"), "audioOnly": data.get("audioOnly", False)}
                room["playback"]["position_ms"] = 0
                await broadcast(room, {"type": "media_update", "media": room["media"], "playback": room["playback"]})
            
            elif msg_type == "host_transfer" and room["host_id"] == client_id:
                target = data.get("targetUserId")
                if target in room["participants"]:
                    room["host_id"] = target
                    room["co_hosts"].discard(target)
                    await broadcast(room, {"type": "participants", "participants": participant_payload(room), "hostId": room["host_id"]})
            
            elif msg_type == "co_host" and room["host_id"] == client_id:
                target = data.get("targetUserId")
                if target in room["participants"] and target != room["host_id"]:
                    if data.get("enabled"):
                        room["co_hosts"].add(target)
                    else:
                        room["co_hosts"].discard(target)
                    await broadcast(room, {"type": "participants", "participants": participant_payload(room), "hostId": room["host_id"]})
            
            elif msg_type == "kick_user" and room["host_id"] == client_id:
                target = data.get("targetUserId")
                if target in room["participants"]:
                    await room["participants"][target]["socket"].send_json({"type": "user_kicked", "userId": target})
                    room["participants"].pop(target)
                    await broadcast(room, {"type": "participants", "participants": participant_payload(room), "hostId": room["host_id"]})
            
            elif data.get("action") in ["play", "pause", "seek", "sync"] and role_for(room, client_id) in ["host", "co-host"]:
                room["playback"]["position_ms"] = int(data.get("time", room["playback"]["position_ms"]))
                room["playback"]["is_playing"] = data.get("isPlaying", room["playback"]["is_playing"])
                await broadcast(room, {"type": "sync_event", **data, "by": username}, exclude=client_id)
    
    except WebSocketDisconnect:
        pass
    finally:
        room["participants"].pop(client_id, None)
        if not room["participants"]:
            rooms.pop(room_id, None)
        elif room["host_id"] == client_id and room["participants"]:
            room["host_id"] = next(iter(room["participants"]))
            await broadcast(room, {"type": "participants", "participants": participant_payload(room), "hostId": room["host_id"]})
