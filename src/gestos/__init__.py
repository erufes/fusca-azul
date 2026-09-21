import os
import socket
import sys

import qrcode
import uvicorn

PORT = 8080


def page_url():
    """Use the outgoing network interface without sending any network packets."""
    if url := os.environ.get("FUSCA_URL"):
        return url
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
            connection.connect(("192.0.2.1", 80))
            address = connection.getsockname()[0]
    except OSError:
        address = "127.0.0.1"
    return f"http://{address}:{PORT}/"


def print_page_qr(url):
    print(f"\nFusca Azul — {url}\n")
    qr = qrcode.QRCode(border=4)
    qr.add_data(url)
    qr.make(fit=True)
    # Fixed colors keep the QR readable on light and dark terminals.
    qr.print_ascii(tty=sys.stdout.isatty(), invert=True)
    if url.startswith("http://127.0.0.1:"):
        print("Sem endereço de rede disponível. Este link só abre neste computador.")
    else:
        print("Escaneie com um celular conectado à mesma rede.")
    if url.startswith("http://"):
        print("Para usar a câmera no celular, a página precisa de HTTPS.")
    print(flush=True)


def main():
    print("Iniciando o servidor de gestos para o Fusca Azul...")
    print_page_qr(page_url())
    uvicorn.run(
        "gestos.server:app", host="0.0.0.0", port=PORT, reload=True,
        access_log=False, log_level=os.environ.get("FUSCA_LOG_LEVEL", "info").lower(),
    )
