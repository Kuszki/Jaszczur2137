# coding=UTF-8

from random import random

class DHT22:

	def __init__(self, pin): pass
	
	def temperature(self): return 10 * random() + 15
	def humidity(self): return 75 * random() + 25
