# coding=UTF-8

from sensor import sensor
from time import time

class dthsens:

	class __dummy: pass

	def __init__(self, sens, tname, hname, var):

		self.sens = sens
		self.last = 0

		self.tobj = self.__dummy()
		self.tobj.value = sens.temperature
		self.tobj.update = self.update

		self.hobj = self.__dummy()
		self.hobj.value = sens.humidity
		self.hobj.update = self.update

		self.tsens = sensor(tname, self.tobj, var, 10)
		self.hsens = sensor(hname, self.hobj, var, 10)

	def update(self, now = None):

		if now is None: now = time()

		if now - self.last >= 2:
			self.sens.measure()
			self.last = now

	def sensors(self):

		return {
			self.tsens.id(): self.tsens,
			self.hsens.id(): self.hsens,
		}

	def temperature(self): return self.tsens.value()

	def humidity(self): return self.hsens.value()
