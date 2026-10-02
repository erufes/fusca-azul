import math
from types import SimpleNamespace
import unittest

from gestos.recognition import identificar_comando
from gestos.modes import ModeControl


def hand(thumb=False, index=False, middle=False, ring=False, pinky=False):
	points = [SimpleNamespace(x=0.0, y=0.0) for _ in range(21)]
	points[2] = SimpleNamespace(x=-.2, y=.25)
	points[4] = SimpleNamespace(x=-.55 if thumb else 0, y=.4 if thumb else .25)
	for x, base, tip, extended in [(-.15,5,8,index), (0,9,12,middle), (.15,13,16,ring), (.3,17,20,pinky)]:
		points[base] = SimpleNamespace(x=x, y=.55)
		points[tip] = SimpleNamespace(x=x, y=1.05 if extended else .25)
	return points


class RecognitionTests(unittest.TestCase):
	def test_gestures_are_invariant_to_mirror_scale_and_rotation(self):
		examples = [((1,1,1,1,1), 'FRENTE'), ((0,0,0,0,1), 'DIREITA'),
					((1,0,0,0,0), 'ESQUERDA'), ((0,1,1,0,0), 'RE'),
					((0,0,0,0,0), 'PARAR'), ((0,1,0,0,1), 'TROCAR_MODO'),
					((1,1,0,0,1), 'TROCAR_MODO'),
					((1,1,0,0,0), 'AGUARDANDO'), ((0,1,0,0,0), 'AGUARDANDO')]
		for fingers, expected in examples:
			for mirror in [-1, 1]:
				for angle in [0, .6, 1.5]:
					points = hand(*fingers)
					for p in points:
						x, y = p.x * mirror, p.y
						p.x = .5 + .2 * (x * math.cos(angle) - y * math.sin(angle))
						p.y = .5 + .2 * (x * math.sin(angle) + y * math.cos(angle))
					with self.subTest(fingers=fingers, mirror=mirror, angle=angle):
						self.assertEqual(identificar_comando(points), expected)

	def test_missing_or_degenerate_hand(self):
		self.assertEqual(identificar_comando([]), 'NENHUMA_MAO')
		self.assertEqual(identificar_comando([SimpleNamespace(x=0,y=0)] * 21), 'AGUARDANDO')

	def test_rock_hold_survives_thumb_movement(self):
		control = ModeControl()
		changes = []
		for frame in range(21):
			points = hand(thumb=bool(frame % 2), index=True, pinky=True)
			command = identificar_comando(points)
			self.assertEqual(command, 'TROCAR_MODO')
			changes.append(control.update(command, frame / 10))
		self.assertEqual(sum(changes), 1)
		self.assertEqual(control.mode, 'AUTO')

	def test_rock_requires_middle_and_ring_folded(self):
		for thumb in (False, True):
			for middle, ring in ((True, False), (False, True), (True, True)):
				with self.subTest(thumb=thumb, middle=middle, ring=ring):
					self.assertNotEqual(identificar_comando(hand(thumb, True, middle, ring, True)), 'TROCAR_MODO')


class ModeTests(unittest.TestCase):
	def test_hold_release_and_second_toggle(self):
		control = ModeControl()
		changes = [control.update('TROCAR_MODO', i / 10) for i in range(51)]
		self.assertEqual(sum(changes), 1)
		self.assertTrue(changes[10])
		self.assertEqual(control.mode, 'AUTO')
		# A single noisy frame must not rearm the mode switch.
		control.update('AGUARDANDO', 5.1)
		for i in range(52, 71):
			self.assertFalse(control.update('TROCAR_MODO', i / 10))
		for i in range(71, 78):
			control.update('PARAR', i / 10)
		changes = [control.update('TROCAR_MODO', i / 10) for i in range(78, 91)]
		self.assertEqual(sum(changes), 1)
		self.assertEqual(control.mode, 'GESTOS')

	def test_pause_and_missing_hand_interrupt_hold(self):
		control = ModeControl()
		control.update('TROCAR_MODO', 0)
		control.update('TROCAR_MODO', .4)
		self.assertFalse(control.update('TROCAR_MODO', 3))
		control.update('NENHUMA_MAO', 3.1)
		self.assertFalse(control.update('TROCAR_MODO', 3.2))
		self.assertEqual(control.mode, 'GESTOS')
		self.assertEqual(ModeControl().mode, 'GESTOS')
