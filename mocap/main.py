import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time
from gestos import gestos

base_options = python.BaseOptions(model_asset_path="utils/hand_landmarker.task")

options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_hands=2,                        
    min_hand_detection_confidence=0.5,  # confiança mínima pra detectar
    min_tracking_confidence=0.3         # confiança mínima pra rastrear
)

webcam = cv2.VideoCapture(0) # Abre a webcam. 0 = câmera padrão do sistema
webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 420)

with vision.HandLandmarker.create_from_options(options) as landmarker:
    while webcam.isOpened():
        ret, frame = webcam.read() # ret → booleano: True se o frame foi capturado com sucesso,  frame → a imagem em si (ndarray NumPy de shape (altura, largura, 3))

        if not ret:
            print("Captura não encontrada")
            break
        
        frame = cv2.flip(frame, 1)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        timestamp = int(time.time() * 1000)

        resultado = landmarker.detect_for_video(mp_image, timestamp)

        if resultado.hand_landmarks:
            for hand in (resultado.hand_landmarks):
                for landmark in hand:
                    h, w, _ = frame.shape
                    cx, cy = int(landmark.x * w), int(landmark.y * h)
                    cv2.circle(frame, (cx, cy), 10, (0, 255, 0), -1)
                    
                    g = gestos(hand)

                    if g.mao_aberta():
                        print("Aberta")

                    elif g.mao_fechada():
                        print("Fechada")
                    else:
                        print("Gesto nao conhecido")    
        else:
            print("Mao nao detectada")

        cv2.imshow("Feed", frame) # Exibe o frame numa janela chamada "Feed", Se a janela não existir, cria automaticamente
        cv2.waitKey(1) # Processa eventos

        if cv2.getWindowProperty("Feed", cv2.WND_PROP_VISIBLE) < 1:
            break

webcam.release() # Libera a câmera para outros programas poderem usá-la
cv2.destroyAllWindows() # Fecha todas as janelas abertas pelo OpenCV