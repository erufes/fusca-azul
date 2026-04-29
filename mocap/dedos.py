import math

def distancia(p1, p2):
    return math.hypot(p2.x - p1.x, p2.y - p1.y)

def indicador_levantado(hand) -> bool:
    palma = distancia(hand[0], hand[5])
    dedo = distancia(hand[0], hand[8])
    
    return dedo > palma * 1.3

def medio_levantado(hand) -> bool:
    palma = distancia(hand[0], hand[9])
    dedo = distancia(hand[0], hand[12])

    return dedo > palma * 1.3

def anelar_levantado(hand) -> bool: 
    palma = distancia(hand[0], hand[13])
    dedo = distancia(hand[0], hand[16])

    return dedo > palma * 1.3

def mindinho_levantado(hand) -> bool:
    palma = distancia(hand[0], hand[17])
    dedo = distancia(hand[0], hand[20])

    return dedo > palma * 1.3

def polegar_levantado(hand, lado) -> bool:
    ponta = hand[4]
    junta = hand[3]
    base = hand[2]

    lateral = abs(ponta.x - base.x)

    if lado == "Right":
        direcao = ponta.x > junta.x
    else:
        direcao = ponta.x < junta.x

    return (
        lateral > 0.05
        and direcao
    )