import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time
from gestos import gestos
from requisicoes import enviar_comando

# Variaveis para checar o estado atual do programa

last_send = 0 # Úlimo envio de requisição
ultimo_toggle = 0 # Modo atual
cooldown_toggle = 3.0 #tempo de demora da troca de modos
modoAutomatico = False

base_options = python.BaseOptions(
    model_asset_path="utils/hand_landmarker.task"
)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_hands=1, # Num de mãos                    
    min_hand_detection_confidence=0.5,  # confiança mínima pra detectar
    min_tracking_confidence=0.3         # confiança mínima pra rastrear
)

webcam = cv2.VideoCapture(0) # Abre a webcam. 0 = câmera padrão do sistema

# Resolução
webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

last_send = enviar_comando("modo_gesto", last_send)

# Event Loop
with vision.HandLandmarker.create_from_options(options) as landmarker:
    while webcam.isOpened():

        action = None

        ret, frame = webcam.read() # ret → booleano: True se o frame foi capturado com sucesso,  frame → a imagem em si (ndarray NumPy de shape (altura, largura, 3))

        if not ret:
            print("Captura não encontrada")
            break
        
        frame = cv2.flip(frame, 1)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        timestamp = int(time.time() * 1000)

        resultado = landmarker.detect_for_video(mp_image, timestamp)

        if resultado.hand_landmarks:
            for i, hand in enumerate(resultado.hand_landmarks):

                lado = resultado.handedness[i][0].category_name # Mão esquerda/direita
                gesto = gestos(hand, lado)

                # DESENHA landmarks
                for landmark in hand:
                    h, w, _ = frame.shape
                    cx, cy = int(landmark.x * w), int(landmark.y * h)
                    cv2.circle(frame, (cx, cy), 10, (0, 255, 0), -1)

                # DETECTA gesto (FORA do loop dos landmarks) (estava checando 21 vezes por frame o que crashava o programa)
                if modoAutomatico:
                    if gesto.fazOL() and time.time() - ultimo_toggle > cooldown_toggle:
                        action = "modo_gesto"
                        modoAutomatico = False
                        ultimo_toggle = time.time()
                        print("Modo Gestos")

                else:
                    if gesto.fazOL():
                        if time.time() - ultimo_toggle > cooldown_toggle:
                            action = "modo_auto"
                            modoAutomatico = True
                            ultimo_toggle = time.time()
                            print("Modo auto")

                    elif gesto.frente():
                        action = "frente"

                    elif gesto.parado():
                        action = "parar"

                    elif gesto.re():
                        action = "re"

                    elif gesto.direita():
                        action = "direita"

                    elif gesto.esquerda():
                        action = "esquerda"

                    #checa ultimo action e tempo do ultimo comando para não sobrecarregar
                if action is not None:
                     if time.time() - last_send > 0.1:
                        last_send = enviar_comando(action, last_send)
        
        #bloco abaixo movido para esquerda para não crashar quando não há mao detectada
        cv2.imshow("Feed", frame) # Exibe o frame numa janela chamada "Feed", Se a janela não existir, cria automaticamente
        cv2.waitKey(1) # Processa eventos

        if cv2.getWindowProperty("Feed", cv2.WND_PROP_VISIBLE) < 1:
            break

webcam.release() # Libera a câmera para outros programas poderem usá-la
cv2.destroyAllWindows() # Fecha todas as janelas abertas pelo OpenCV
