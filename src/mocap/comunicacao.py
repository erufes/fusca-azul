import requests
import time

ESP32_IP = "192.168.0.135"  # ← IP do esp

def enviar_comando(comando, last_send):
    try:
        requests.get(f"http://{ESP32_IP}/cmd?action={comando}", timeout=0.1)

        last_send = time.time()
        return last_send
    
    except requests.exceptions.RequestException as e:
            print(f"Erro ao enviar: {e}")
            last_send = time.time()
            return last_send