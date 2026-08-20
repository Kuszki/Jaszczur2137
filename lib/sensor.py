# coding=UTF-8

from micropython import const
from gc import collect
from json import load

_FMT = const('%0.1f %s')

class mavg:

	def __init__(self, size = 30):

		self.buf = [0] * size
		self.pos = 0
		self.count = 0
		self.sum = 0
		self.size = size

	def update(self, value):

		self.sum -= self.buf[self.pos]

		self.buf[self.pos] = value
		self.sum += value

		self.pos += 1
		self.pos %= self.size

		if self.count < self.size:
			self.count += 1

		return self.sum / self.count

	def value(self):

		return self.sum / self.count

class sensor:

	def __init__(self, uid, sen, var, avg = 15):

		self.avg = mavg(avg)
		self.sen = sen
		self.uid = uid
		self.var = var
		self.nam = uid
		self.uni = str()
		self.fmt = _FMT

		self.load()

	def __str__(self): return self.fmt % (self.value(), self.uni)

	def value(self): return self.avg.value()

	def name(self): return self.nam

	def format(self): return self.fmt

	def unit(self): return self.uni

	def id(self): return self.uid

	def update(self):

		self.sen.update()

		val = self.sen.value()
		val = self.avg.update(val)

		self.var[self.uid] = val

	def load(self):

		try:
			with open('/sens/%s.json' % self.uid, 'r') as f:

				conf = load(f)

				try: self.nam = str(conf['name'])
				except: pass

				try: self.uni = str(conf['unit'])
				except: pass

				try: self.fmt = str(conf['format'])
				except: pass

		except: pass
		finally: collect()

	def dump(self): return {

			'uid': self.id(),
			'name': self.name(),
			'value': self.value(),
			'unit': self.unit(),
			'format': self.format(),
			'text': str(self)
		}
