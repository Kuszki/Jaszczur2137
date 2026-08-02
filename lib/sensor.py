# coding=UTF-8

from json import load

class mavg:

	def __init__(self, size = 30):

		self.size = size
		self.buf = [0] * size
		self.pos = 0
		self.count = 0
		self.sum = 0

	def update(self, value):

		self.sum -= self.buf[self.pos]

		self.buf[self.pos] = value
		self.sum += value

		self.pos = (self.pos + 1) % self.size

		if self.count < self.size:
			self.count += 1

		return self.sum / self.count

	def value(self):

		return self.sum / self.count

class sensor:

	def __init__(self, uid, sen, var):

		try: conf = load(open('/sens/%s.json' % uid, 'r'))
		except: conf = dict()

		try: self.nam = str(conf['name'])
		except: self.nam = uid

		try: self.uni = str(conf['unit'])
		except: self.uni = str()

		try: self.fmt = str(conf['format'])
		except: self.fmt = "%0.1f %s"

		self.avg = mavg(15)
		self.sen = sen
		self.uid = uid
		self.var = var

		self.update()

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

	def dump(self): return {

			'uid': self.id(),
			'name': self.name(),
			'value': self.value(),
			'unit': self.unit(),
			'format': self.format(),
			'text': str(self)

		}
