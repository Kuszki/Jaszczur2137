# coding=UTF-8

import time, ntptime, json, machine, os, gc, esp32

class driver:

	def __init__(self, outs, sens, var):

		try: self.tasks = json.load(open('./etc/jobs.json', 'r'))
		except: self.tasks = dict()
		else: gc.collect()
		finally: self.lastt = 0

		for k in self.tasks:
			if int(k) >= self.lastt:
				self.lastt = int(k) + 1

		try: settings = json.load(open('./etc/driver.json', 'r'))
		except: settings = dict()
		else: gc.collect()

		try: self.driver = settings['main']['driver']
		except: self.driver = False

		try: self.tzone = settings['time']['zone']
		except: self.tzone = 0

		try: self.loop = settings['time']['loop']
		except: self.loop = 30

		try: self.meas = settings['time']['meas']
		except: self.meas = 30

		try: self.sync = settings['time']['sync']
		except: self.sync = 36000

		try: self.psize = settings['plot']['size']
		except: self.psize = 72

		try: self.page = settings['plot']['age']
		except: self.page = 259200

		try: self.lsize = settings['logs']['size']
		except: self.lsize = 25

		try: self.lage = settings['logs']['age']
		except: self.lage = 259200

		try: self.wtok = settings['outdor']['token']
		except: self.wtok = str()

		try: self.wpla = settings['outdor']['place']
		except: self.wpla = str()

		del settings; gc.collect()

		self.ptime = int(self.page / self.psize)
		self.ltime = int(self.lage / self.lsize)

		self.reboot = False

		self.last_loop = 0
		self.last_meas = 0
		self.last_sync = 0

		self.tp_save = 0
		self.tl_save = 0

		self.outs = outs
		self.sens = sens
		self.var = var

		self.last_boot = self.on_time(time.time())
		self.save_logs('boot', None, machine.reset_cause())
		self.on_startup(self.last_boot)

	def save_settings(self):

		with open('./etc/driver.json', 'w') as f:
			json.dump(self.get_conf(), f)

	def save_tasks(self):

		with open('./etc/jobs.json', 'w') as f:
			json.dump(self.get_tasks(), f)

	def save_outs(self):

		for o in self.outs: o.save()

	def save_history(self, t, now = None):

		if now == None: now = time.time()

		for k, y in t.items():

			val = round(y.value(), 2)
			data = { 't': now, 'y': val }
			path = './var/%s' % k
			v = dict()
			save = True

			try:
				with open(path, 'r') as f:
					v = json.load(f)

			except:
				v['uid'] = k
				v['label'] = y.name()
				v['unit'] = y.unit()
				v['last'] = now
				v['data'] = [ data ]

			else:
				if now - v['last'] >= self.ptime:

					v['data'].append(data)
					v['last'] = now

				else: save = False

			if save:
				with open(path, 'w') as f:
					json.dump(v, f)

			del v, path, data

	def save_logs(self, k, u, s, now = None):

		if now == None: now = time.time()

		try: logs = json.load(open('./etc/log.json', 'r'))
		except: logs = list()

		while len(logs) >= self.lsize: logs.pop(-1)

		logs.insert(0, { 't': now, 'k': k, 'u': u, 's': s })

		with open('./etc/log.json', 'w') as f: json.dump(logs, f)

	def set_power(self, v):

		try:
			uid = str(v['uid'])
			pwr = int(v['power'])
		except:
			return False

		if uid != "all":
			try: outs = [ self.outs[uid] ]
			except: return False
		else: outs = self.outs.values()

		for out in outs:
			if out.status() != pwr:
				self.save_logs('drv', out.name(), 0)
				self.save_logs('pwr', out.name(), pwr)
				out.update(state = pwr, driver = False)
			elif out.driver():
				self.save_logs('drv', out.name(), 0)
				out.update(driver = False)

			if out.changed(): out.save()

		return True

	def set_driver(self, v):

		try:
			uid = str(v['uid'])
			drv = int(v['driver'])
		except:
			return False

		if uid != "all":
			try: outs = [ self.outs[uid] ]
			except: return False
		else: outs = self.outs.values()

		for out in outs:
			if out.driver() != drv:
				self.save_logs('drv', out.name(), drv)
				out.update(driver = drv)

			if out.changed(): out.save()

		return True

	def set_scripts(self, v):

		if not len(v): return False
		else: ok = True

		for k, s in v.items():

			if k not in self.outs: ok = False
			else:

				try:
					out = self.outs[k]
					out.update(script = s)
					out.save()

				except:
					ok = False

		return ok

	def set_tasks(self, v):

		if not len(v): return False
		else: ok = True

		for k, s in v.items():

			if 'del' in s and s['del']:

				try: del self.tasks[k]
				except: ok = False

			else:

				if k not in self.tasks:
					self.tasks[k] = dict()

				try:

					self.tasks[k]['uid'] = str(s['uid'])
					self.tasks[k]['when'] = int(s['when'])
					self.tasks[k]['job'] = int(s['job'])

				except:
					ok = False

		if ok: self.save_tasks()

		return ok

	def set_params(self, v):

		if not len(v): return False
		else: ok = True; num = 0

		try:

			if 'psize' in v:

				val = int(v['psize'])

				if 30 <= val <= 150:
					self.psize = val
					self.ptime = int(self.page / self.psize)
					self.tp_save = 0
					num = num + 1
				else: ok = False

			if 'page' in v:

				val = int(v['page'])

				if 1 <= val <= 5:
					self.page = val * 86400
					self.psize = int(self.page / self.ptime)
					self.tp_save = 0
					num = num + 1
				else: ok = False

			if 'ptime' in v:

				val = int(v['ptime'])

				if 15 <= val <= 180:
					self.ptime = val * 60
					self.psize = int(self.page / self.ptime)
					self.tp_save = 0
					num = num + 1
				else: ok = False

			if 'lsize' in v:

				val = int(v['lsize'])

				if 10 <= val <= 100:
					self.lsize = val
					self.ltime = int(self.lage / self.lsize)
					self.tl_save = 0
					num = num + 1
				else: ok = False

			if 'lage' in v:

				val = int(v['lage'])

				if 1 <= val <= 10:
					self.lage = val * 86400
					self.ltime = int(self.lage / self.lsize)
					self.tl_save = 0
					num = num + 1
				else: ok = False

			if 'sync' in v:

				val = int(v['sync'])

				if 5 <= val <= 360:
					self.sync = val * 60
					num = num + 1
				else: ok = False

			if 'tzone' in v:

				val = int(v['tzone'])

				if -12 <= val <= 14:
					self.tzone = val
					num = num + 1
				else: ok = False

			if 'loop' in v:

				val = int(v['loop'])

				if 5 <= val <= 60:
					self.loop = val
					num = num + 1
				else: ok = False

			if 'save' in v:

				self.save_settings()
				num = num + 1

			if 'reboot' in v:

				self.reboot = True
				num = num + 1

			if 'rmlogs' in v:

				try: os.remove('./etc/log.json')
				except: ok = False
				else: num = num + 1

		except: ok = False

		return ok and (num == len(v))

	def get_outputs(self):

		out = list()

		for o in self.outs.values():
			out.append(o.dump())

		return out

	def get_sensors(self):

		out = list()

		for s in self.sens.values():
			out.append(s.dump())

		return out

	def get_units(self):

		out = list()

		for s in self.sens.values():
			if s.unit() not in out:
				out.append(s.unit())

		return out

	def get_devinfo(self):

		try: tmp = esp32.raw_temperature()
		except: tmp = None
		else: tmp = '%00.2f ℃' % ((tmp-32) / 1.8)

		try: mem = gc.mem_free() / 1024
		except: mem = None
		else: mem = '%0.1f kB' % (mem)

		t = time.time()

		dt = t - self.last_boot
		t = t + self.tzone * 3600
		t = time.localtime(t)[0:6]

		udays = dt / 86400; dt %= 86400
		uhours = dt / 3600; dt %= 3600
		umins = dt / 60; dt %= 60

		return \
		{
			'Godzina': '%d:%02d:%02d' % (t[3], t[4], t[5]),
			'Data': '%02d.%02d.%04d' % (t[2], t[1], t[0]),
			'Czas pracy': '%dd %dh %dm' % (udays, uhours, umins),

			'Dostępna pamięć RAM': mem,
			'Temperatura CPU': tmp,
		}

	def get_timing(self):

		return \
		{
			'Uruchomienie': self.last_boot,
			'Czas': self.last_sync,
			'Wykres': self.tp_save,
			'Historia': self.tl_save
		}

	def get_params(self):

		return \
		{
			'tzone': self.tzone,
			'loop': self.loop,
			'psize': self.psize,
			'lsize': self.lsize,

			'page': int(self.page / 86400),
			'lage': int(self.lage / 86400),
			'ptime': int(self.ptime / 60),

			'sync': int(self.sync / 60),
		}

	def get_conf(self):

		return \
		{
			'time':
			{
				'zone': self.tzone,
				'loop': self.loop,
				'sync': self.sync,
			},
			'plot':
			{
				'size': self.psize,
				'age': self.page
			},
			'logs':
			{
				'size': self.lsize,
				'age': self.lage
			}
		}

	def get_hist(self):

		return os.listdir('./var')

	def get_scheds(self):

		return self.schedules

	def get_tasks(self):

		return self.tasks

	def get_tzone(self):

		return self.tzone

	def get_uids(self, v):

		if 'task' in v:
			self.lastt += 1
			return self.lastt

		return None

	def on_time(self, now):

		try:

			ntptime.settime()
			now = time.time()

		except: self.last_sync += 30
		else: self.last_sync = now

		return now

	def on_startup(self, now):

		null = { 't': now, 'y': None }
		hist = os.listdir('./var')

		for l in hist:

			path = './var/%s' % l
			save = False

			try:

				with open(path, 'r') as f: v = json.load(f)

				if now - v['last'] >= self.ptime and v['data'][-1]['y'] != None:
					v['data'].append(null); save = True

				if now - v['data'][-1]['t'] >= self.page: v['data'].clear()
				else:
					while now - v['data'][0]['t'] >= self.page:
						v['data'].pop(0); save = True

				if not len(v['data']): os.remove(path)
				elif save:
					with open(path, 'w') as f: json.dump(v, f)

			except: os.remove(path)

	def on_task(self, now):

		now = now + self.tzone * 3600
		dels = list()

		for k in self.tasks:

			uid = self.tasks[k]['uid']
			when = self.tasks[k]['when']
			job = self.tasks[k]['job']

			if now - when > 3*self.loop or uid not in self.outs: dels.append(k)
			elif now - when >= 0:

				if job == 0: self.outs[uid].update(state = 0, driver = 0)
				elif job == 1: self.outs[uid].update(state = 1, driver = 0)
				elif job == 2: self.outs[uid].update(driver = 1)

				if self.outs[uid].changed(): self.outs[uid].save()

				dels.append(k)

		for k in dels: del self.tasks[k]

		if len(dels): self.save_tasks()

	def on_hist(self, now):

		self.save_history(self.sens, now)
		self.tp_save = now

	def on_logs(self, now):

		try: logs = json.load(open('./etc/log.json', 'r'))
		except: return None
		else: save = False
		finally:

			self.tl_save = now
			now -= now % 86400

		if now - logs[0]['t'] >= self.lage: logs = []
		else:
			while now - logs[-1]['t'] >= self.lage:
				logs.pop(-1)
				save = True

			while len(logs) > self.lsize:
				logs.pop(-1)
				save = True

		if not len(logs): os.remove('./etc/log.json')
		elif save:
			with open('./etc/log.json', 'w') as f:
				json.dump(logs, f)

	def on_loop(self):

		if self.reboot: return machine.reset()
		else: now = time.time()

		if now - self.last_loop >= 1:
			for s in self.sens.values(): s.update()

		if now - self.last_sync >= self.sync:
			now = self.on_time(now)

		if now - self.last_loop >= self.loop:

			dt = now + self.tzone * 3600
			t = time.localtime(dt)[0:7]

			self.var['t'] = t[3]*60 + t[4]

			self.var['h'] = t[3]
			self.var['m'] = t[4]

			self.var['day'] = t[2]
			self.var['mon'] = t[1]
			self.var['year'] = t[0]

			self.var['wday'] = t[6] + 1

			self.last_loop = now

			if len(self.tasks) > 0: self.on_task(now)

			for o in self.outs.values():
				if not o.driver(): continue

				try:
					old = o.status()
					new = o.compute()
				except Exception as e:
					self.save_logs('err', o.name(), str(e))
					o.update(driver = False, state = o.default())
					old = new = None

				if old != new:
					self.save_logs('pwr', o.name(), int(new))

		if now - self.tp_save >= self.ptime:
			self.on_hist(now)

		if now - self.tl_save >= self.ltime:
			self.on_logs(now)
