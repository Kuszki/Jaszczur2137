# coding=UTF-8

from time import ticks_us, ticks_diff
from machine import Pin

class encoder:

	def __init__(self, a, b, time = 750):

		self.pin_a = a
		self.pin_b = b

		self.up_a = 0
		self.up_b = 0

		self.down_a = 0
		self.down_b = 0

		self.time = time
		self.val = 0

		a.irq(self._irq, Pin.IRQ_RISING | Pin.IRQ_FALLING)
		b.irq(self._irq, Pin.IRQ_RISING | Pin.IRQ_FALLING)

	def _irq(self, pin):

		if pin is self.pin_a:
			if pin.value():
				self.up_a = ticks_us()
			else:
				self.down_a = ticks_us()
				self.up_a = 0

		elif pin is self.pin_b:
			if pin.value():
				self.up_b = ticks_us()
			else:
				self.down_b = ticks_us()
				self.up_b = 0

		if self.up_a and self.down_a and self.up_b and self.down_b:

			time_a = ticks_diff(self.up_a, self.down_a)
			time_b = ticks_diff(self.up_b, self.down_b)

			if time_a > self.time and time_b > self.time:

				if time_a > time_b: self.val += 1
				elif time_a < time_b: self.val -= 1

			self.up_a = self.up_b = 0
			self.down_a = self.down_b = 0

	def value(self): return self.val
