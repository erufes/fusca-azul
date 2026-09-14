import cv2
import numpy as np
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from pathlib import Path

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.websocket("/ws/video")
async def websocket_video(websocket: WebSocket):
    await websocket.accept()
    print("Navegador conectado!")

    try:
        while True:
            bytes_img = await websocket.receive_bytes()
            nparr = np.frombuffer(bytes_img, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            await websocket.send_text("frame recebido e analizado")

    except WebSocketDisconnect:
        print("Navegador desconectado!")