"""Session mode selection, independent of image processing."""
from time import monotonic


class ModeControl:
	"""One mode change per held rock sign, rearmed after a stable release."""
	HOLD_SECONDS = 1.0
	RELEASE_SECONDS = 0.5
	MAX_FRAME_GAP = 0.5

	def __init__(self):
		self.mode = "GESTOS"
		self.hold_since = None
		self.release_since = None
		self.latched = False
		self.last_frame = None

	def update(self, command, now=None):
		now = monotonic() if now is None else now
		if self.last_frame is not None and now - self.last_frame > self.MAX_FRAME_GAP:
			self.hold_since = None
			self.release_since = None
		self.last_frame = now
		if command != "TROCAR_MODO":
			self.hold_since = None
			if self.release_since is None:
				self.release_since = now
			if now - self.release_since >= self.RELEASE_SECONDS:
				self.latched = False
			return False
		self.release_since = None
		if self.latched:
			return False
		if self.hold_since is None:
			self.hold_since = now
		if now - self.hold_since < self.HOLD_SECONDS:
			return False
		self.mode = "AUTO" if self.mode == "GESTOS" else "GESTOS"
		self.latched = True
		return True
