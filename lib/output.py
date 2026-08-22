# coding=UTF-8

from json import load, dump
from parser import script
from gc import collect

class output:

	def __init__(self, uid, out, var):

		self.drv = False
		self.code = None
		self.val = False
		self.nam = uid

		self.out = out
		self.uid = uid
		self.var = var
		self.vde = self.val
		self.cha = False

		self.load()

		out.value(self.val)
		var[uid] = self.val

	def __str__(self): return "ON" if bool(self) else "OFF"

	def __bool__(self): return self.status()

	def update(self, state = None, driver = None, script = None):

		if state is not None and state < 0: state = self.vde

		if script is not None and self.script() != script:
			self.code.update(script)
			self.cha = True

		if driver is not None and self.driver() != driver:
			self.drv = driver
			self.cha = True

		if state is not None and self.status() != state:

			state = bool(int(state))

			self.out.value(state)
			self.val = state
			self.var[self.uid] = state

	def compute(self):

		old = self.status()
		new = self.code.compute()

		if old != new:
			self.update(state = new)

		return new

	def status(self): return self.val

	def driver(self): return self.drv

	def id(self): return self.uid

	def name(self): return self.nam

	def changed(self): return self.cha

	def default(self): return self.vde

	def script(self): return self.code.script()

	def dump(self): return {

			'uid': self.id(),
			'name': self.name(),
			'status': self.status(),
			'code': self.script(),
			'driver': self.driver(),
			'default': self.default()

		}

	def load(self):

		try:
			with open('/outs/%s.json' % self.uid, 'r') as f:

				conf = load(f)

				try: self.code = script(conf['code'], self.var, None, True)
				except: self.code = script("0", self.var, None, True)

				try: self.drv = int(conf['driver'])
				except: pass

				try: self.val = int(conf['default'])
				except: pass

				try: self.nam = str(conf['name'])
				except: pass

		except: pass
		finally: collect()

	def save(self, force = False):

		if not self.cha and not force: return None
		else: self.cha = False

		v = {
			'name': self.name(),
			'code': self.script(),
			'driver': self.driver(),
			'default': self.default()
		}

		with open('/outs/%s.json' % self.uid, 'w') as f: dump(v, f)
