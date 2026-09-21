import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# --- CONFIGURAÇÃO DA NOVA API DO MEDIAPIPE ---
# Aponta para o arquivo .task que você acabou de baixar
model_path = str(BASE_DIR / "model/hand_landmarker.task")

base_options = python.BaseOptions(model_asset_path=model_path)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.7
)
# Inicializa o detector
detector = vision.HandLandmarker.create_from_options(options)

def identificar_comando(hand_landmarks):
    """
    Compara a posição Y das pontas com as bases.
    Na nova API, hand_landmarks já é uma lista direta de pontos.
    """
    pontas = [8, 12, 16, 20]
    bases = [6, 10, 14, 18]
    dedos_levantados = 0
    
    for ponta, base in zip(pontas, bases):
        if hand_landmarks[ponta].y < hand_landmarks[base].y:
            dedos_levantados += 1
            
    if dedos_levantados >= 3:
        return "FRENTE" 
    elif dedos_levantados == 0:
        return "PARAR"  
    else:
        return "AGUARDANDO" 

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.websocket("/ws/video")
async def websocket_video(websocket: WebSocket):
    await websocket.accept()
    include_landmarks = websocket.query_params.get("landmarks") == "1"
    print("Conexão estabelecida! Cérebro ativado (Nova API).")
    
    try:
        while True:
            bytes_img = await websocket.receive_bytes()
            nparr = np.frombuffer(bytes_img, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR) if nparr.size else None
            if frame is None:
                if include_landmarks:
                    await websocket.send_json({"error": "Imagem inválida", "command": "NENHUMA_MAO", "landmarks": []})
                else:
                    await websocket.send_text("NENHUMA_MAO")
                continue
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # A nova API exige que a imagem seja convertida para o formato mp.Image
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            
            # Detecta as mãos
            resultados = detector.detect(mp_image)
            
            comando = "NENHUMA_MAO"
            
            # O formato de resposta mudou para resultados.hand_landmarks
            if resultados.hand_landmarks:
                for hand_landmarks in resultados.hand_landmarks:
                    comando = identificar_comando(hand_landmarks)
                    print(f"Comando detectado: {comando}")
            
            if include_landmarks:
                landmarks = resultados.hand_landmarks[0] if resultados.hand_landmarks else []
                await websocket.send_json({
                    "command": comando,
                    "landmarks": [{"x": point.x, "y": point.y} for point in landmarks],
                })
            else:
                # Preserve the text protocol for existing clients.
                await websocket.send_text(comando)
            
    except WebSocketDisconnect:
        print("Navegador desconectado.")
