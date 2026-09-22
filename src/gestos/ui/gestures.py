"""Presentation labels shared by the live view and the tutorial."""
from dataclasses import dataclass


@dataclass(frozen=True)
class GestureGuide:
	command: str
	symbol: str
	label: str
	pose: str
	fingers: tuple[bool, bool, bool, bool, bool]


GESTURES = (
	GestureGuide("FRENTE", "↑", "Em frente", "Mão aberta, com os cinco dedos estendidos.", (True, True, True, True, True)),
	GestureGuide("PARAR", "■", "Parado", "Punho fechado, com todos os dedos recolhidos.", (False, False, False, False, False)),
	GestureGuide("DIREITA", "→", "Direita", "Apenas o mindinho levantado; os demais dedos recolhidos.", (False, False, False, False, True)),
	GestureGuide("ESQUERDA", "←", "Esquerda", "Apenas o polegar estendido; os demais dedos recolhidos.", (True, False, False, False, False)),
	GestureGuide("RE", "↓", "Para trás", "Indicador e médio em V; os demais dedos recolhidos.", (False, True, True, False, False)),
	GestureGuide("TROCAR_MODO", "↔", "Troca de modo", "Gesto de rock: indicador e mindinho levantados, polegar recolhido.", (False, True, False, False, True)),
)

COMMANDS = {gesture.command: (gesture.symbol, gesture.label) for gesture in GESTURES}
COMMANDS.update({
	"AGUARDANDO": ("…", "Aguardando"),
	"NENHUMA_MAO": ("—", "Nenhuma mão"),
})
