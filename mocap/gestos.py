from dedos import indicador_levantado, medio_levantado, anelar_levantado, mindinho_levantado, polegar_levantado

class gestos:
    def __init__(self, hand):
        self.hand = hand

    def mao_aberta(self) -> bool:
        return indicador_levantado(self.hand) and medio_levantado(self.hand) and anelar_levantado(self.hand) and mindinho_levantado(self.hand) and polegar_levantado(self.hand)
    
    def mao_fechada(self):
        return not indicador_levantado(self.hand) and not medio_levantado(self.hand) and not anelar_levantado(self.hand) and not mindinho_levantado(self.hand) and not polegar_levantado(self.hand)