import uvicorn
import uvicorn

def main():

	print("Iniciando o servidor de gestos para o fusca azul...")
	uvicorn.run("gestos.server:app", host="0.0.0.0", port=8080, reload=True)