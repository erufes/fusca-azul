"""Hand geometry and gesture recognition, independent of server state."""
from math import hypot


def distance(a, b):
    return hypot(a.x - b.x, a.y - b.y)


def identificar_comando(hand):
    if len(hand) != 21:
        return "NENHUMA_MAO"
    # Relative distances avoid depending on left/right hand or image mirroring.
    extended = [distance(hand[0], hand[tip]) > 1.3 * distance(hand[0], hand[base])
                for base, tip in [(5, 8), (9, 12), (13, 16), (17, 20)]]
    palm = distance(hand[0], hand[2])
    if palm < 1e-6 or distance(hand[5], hand[17]) < 1e-6:
        return "AGUARDANDO"
    outward = ((hand[4].x - hand[2].x) * (hand[5].x - hand[17].x)
               + (hand[4].y - hand[2].y) * (hand[5].y - hand[17].y)) > 0
    thumb = (distance(hand[0], hand[4]) > palm * 1.3 and outward
             and distance(hand[4], hand[5]) >= palm * 0.52)
    gestures = {
        (True, True, True, True, True): "FRENTE",
        (False, False, False, False, False): "PARAR",
        (False, True, True, False, False): "RE",
        (False, False, False, False, True): "DIREITA",
        (True, False, False, False, False): "ESQUERDA",
        (False, True, False, False, True): "TROCAR_MODO",
    }
    return gestures.get((thumb, *extended), "AGUARDANDO")
