import cv2
import mediapipe as mp
import requests
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time
from gestos import gestos

# Variaveis para checar ultimo comando e tempo do ultimo comando
last_print_action = ""
last_send = 0
last_unknown = False
last_no_hand = False
last_connection_error = False

ultimo_toggle = 0
cooldown_toggle = 2.0 //tempo de demora da troca de modos

ESP32_IP = "192.168.0.139"  # ← IP do esp


modoAutomatico = False


# função para enviar comandos para o ESP32
def enviar_comando(comando):

    global last_send
    global last_connection_error

    try:

        requests.get(
            f"http://{ESP32_IP}/cmd?action={comando}",
            timeout=0.1
        )

        last_send = time.time()
        last_connection_error = False

    except requests.exceptions.RequestException as e:

        if not last_connection_error:

            print(f"Erro ao enviar: {e}")
            last_connection_error = True


base_options = python.BaseOptions(
    model_asset_path="utils/hand_landmarker.task"
)

options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_hands=1,
    min_hand_detection_confidence=0.5,
    min_tracking_confidence=0.3
)

# Abre a webcam. 0 = câmera padrão do sistema
webcam = cv2.VideoCapture(0)

webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)


enviar_comando("modo_gesto")


with vision.HandLandmarker.create_from_options(options) as landmarker:

    while webcam.isOpened():

        action = None

        # captura frame da webcam
        ret, frame = webcam.read()

        if not ret:
            print("Captura não encontrada")
            break

        frame = cv2.flip(frame, 1)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=frame
        )

        timestamp = int(time.time() * 1000)

        resultado = landmarker.detect_for_video(
            mp_image,
            timestamp
        )

        # modo gestos
        if resultado.hand_landmarks:

            last_no_hand = False

            for i, hand in enumerate(resultado.hand_landmarks):

                lado = resultado.handedness[i][0].category_name

                g = gestos(hand, lado)

                # desenha landmarks
                for landmark in hand:

                    h, w, _ = frame.shape

                    cx = int(landmark.x * w)
                    cy = int(landmark.y * h)

                    cv2.circle(
                        frame,
                        (cx, cy),
                        10,
                        (0, 255, 0),
                        -1
                    )

                # detecta gesto
                if(modoAutomatico):
                
                    if g.fazOL() and time.time() - ultimo_toggle > cooldown_toggle:

                        action = "modo_gesto"
                        modoAutomatico = False

                        ultimo_toggle = time.time()

                        last_unknown = False    


                else:
                    
                    if g.fazOL() and time.time() - ultimo_toggle > cooldown_toggle:

                        action = "modo_auto"
                        modoAutomatico = True

                        ultimo_toggle = time.time()

                        last_unknown = False

                    elif g.frente():

                        action = "frente"
                        last_unknown = False

                    elif g.parado():
                        
                        action = "parar"
                        last_unknown = False

                    elif g.re():

                        action = "re"
                        last_unknown = False

                    elif g.direita():

                        action = "direita"
                        last_unknown = False
                        
                    elif g.esquerda(): 

                        action = "esquerda"
                        last_unknown = False

                    else:

                        if not last_unknown:

                            print("Gesto não reconhecido")
                            last_unknown = True

                # printa sem repetir
                if action != last_print_action and action is not None:

                    last_print_action = action
                    print(action)

                # envia comando sem sobrecarregar
                if action is not None:

                    if time.time() - last_send > 0.1:

                        enviar_comando(action)

        else:

            # printa sem repetir se mao nao detectada
            if not last_no_hand:

                print("Mão não detectada")
                last_no_hand = True

        # mostra webcam
        cv2.imshow("Feed", frame)


        # captura tecla
        tecla = cv2.waitKey(1) & 0xFF

        # ativa modo automatico atraves da tecla
        if tecla == ord('a'):

            enviar_comando("modo_auto")

            modoAutomatico = True

            print("Modo automatico")

        # ativa modo gestos atraves da tecla
        elif tecla == ord('g'):

            enviar_comando("modo_gesto")

            modoAutomatico = False

            print("Modo gesto")

        # fecha janela
        if cv2.getWindowProperty(
            "Feed",
            cv2.WND_PROP_VISIBLE
        ) < 1:

            break

# libera webcam
webcam.release()

# fecha janelas
cv2.destroyAllWindows()