class Pin:

	OUT = 1
	IN = 2

	PULL_UP = 1
	PULL_DOWN = 2

	def __init__(self, uid, mode = -1, pull = -1, *, value = None, drive = 0, alt = -1):

		if value is not None: self.val = bool(value)
		else: self.val = False

		self.mode = mode

	def __bool__(self):

		return self.value()

	def value(self, val = None):

		if val is not None: self.val = bool(val)
		elif self.mode == seld.IN: return bool(self.val)
		else: return None

def reset_cause(): return 1
