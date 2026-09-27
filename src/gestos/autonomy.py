"""Conservative navigation from relative inverse depth, never metric distance.

A visible planar floor and a forward/downward camera are required. MiDaS can
miss glass, thin objects, steps and unfamiliar scenes. This is a prototype,
not a replacement for range sensors or a physical emergency stop.
"""
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class Navigation:
	command: str
	reason: str
	confident: bool
	occupancy: tuple = ()


class DepthNavigator:
	def __init__(self):
		self.candidate = "PARAR"
		self.stable = 0
		self.turn_started = None
		self.pause_until = 0
		self.previous_time = None

	def stop(self, reason):
		self.candidate, self.stable, self.turn_started = "PARAR", 0, None
		return Navigation("PARAR", reason, False)

	def analyze(self, frame, depth, now):
		image = cv2.resize(frame, (320, 240))
		heat = np.zeros_like(image)
		if depth.shape != (240, 320) or not np.isfinite(depth).all():
			return image, heat, self.stop("Profundidade inválida")
		gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
		if np.mean(gray < 20) > .65 or np.mean(gray > 245) > .65:
			return image, heat, self.stop("Imagem escura ou superexposta")
		low, high = np.percentile(depth, (5, 95))
		if high - low < 1e-5:
			return image, heat, self.stop("Não foi possível distinguir a profundidade")
		normalized = (depth - low) / (high - low)
		heat = cv2.applyColorMap(np.uint8(np.clip(normalized, 0, 1) * 255), cv2.COLORMAP_INFERNO)
		# On a planar floor, inverse depth grows approximately linearly down the
		# image. The lower quantile rejects nearer obstacles when fitting it.
		y = np.arange(120, 228) / 240
		profile = np.percentile(normalized[120:228, 32:288], 20, axis=1)
		slope, intercept = np.polyfit(y, profile, 1)
		fit_error = np.abs(profile - (slope * y + intercept))
		if slope < .45 or slope > 4 or np.mean(fit_error < .06) < .75:
			return image, heat, self.stop("Piso não identificado; parar")
		expected = (slope * np.arange(240) / 240 + intercept)[:, None]
		residual = normalized - expected
		# Unexpectedly nearer surfaces are obstacles; missing floor is also unsafe.
		blocked = ((residual > .12) | (residual < -.18)).astype(np.uint8)
		blocked = cv2.morphologyEx(blocked, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
		bounds = ((32, 112), (112, 208), (208, 288))
		occupancy = tuple(float(blocked[120:210, a:b].mean()) for a, b in bounds)
		near = float(blocked[198:228, 96:224].mean())
		left, center, right = occupancy
		command, reason = "PARAR", "Caminho bloqueado ou incerto"
		if near > .12:
			reason = "Obstáculo ou desnível na área próxima"
		elif center < .08:
			command, reason = "FRENTE", "Área central livre"
		elif center > .15 and min(left, right) < .08:
			command = "ESQUERDA" if left <= right else "DIREITA"
			reason = "Desviar pela esquerda" if command == "ESQUERDA" else "Desviar pela direita"
		if self.previous_time is not None and now - self.previous_time > .4:
			self.stable = 0
			self.turn_started = None
		self.previous_time = now
		if command != self.candidate:
			self.candidate, self.stable = command, 0
		self.stable += 1
		if command == "PARAR":
			self.turn_started = None
		elif self.stable < 3:
			command, reason = "PARAR", "Confirmando caminho"
		elif now < self.pause_until:
			command, reason = "PARAR", "Reavaliando após desvio"
		elif command in ("ESQUERDA", "DIREITA"):
			if self.turn_started is None:
				self.turn_started = now
			elif now - self.turn_started >= .35:
				self.turn_started = None
				self.pause_until = now + .25
				command, reason = "PARAR", "Reavaliando após desvio"
		else:
			self.turn_started = None
		mask = blocked.astype(bool)
		mask[:120] = False
		mask[228:] = False
		image[mask] = (image[mask].astype(np.float32) * .5 + np.array([40, 40, 220]) * .5).astype(np.uint8)
		for (a, b), value in zip(bounds, occupancy):
			color = (60, 80, 240) if value >= .08 else (245, 175, 100)
			cv2.rectangle(image, (a, 120), (b, 228), color, 2)
			cv2.putText(image, f"{value:.0%}", (a + 4, 140), cv2.FONT_HERSHEY_SIMPLEX, .4, color, 1)
		return image, heat, Navigation(command, reason, True, occupancy)
