# coding=UTF-8

from time import ticks_ms, ticks_diff
from machine import Pin

class encoder:

	def __init__(self, a, b, time = 125):

		self.pin_a = a
		self.pin_b = b

		self.val = 0
		self.time = time
		self.last = ticks_ms()

		a.irq(self._irq, Pin.IRQ_FALLING | Pin.IRQ_RISING)
		b.irq(self._irq, Pin.IRQ_FALLING | Pin.IRQ_RISING)

	def _irq(self, pin):

		a = self.pin_a.value()
		b = self.pin_b.value()

		if a == b: return

		now = ticks_ms()

		if ticks_diff(now, self.last) < self.time: return

		if a and pin is self.pin_a: self.val += 1
		if not b and pin is self.pin_b: self.val -= 1

		self.last = now

	def value(self): return self.val
