# coding=UTF-8

import socket, select, json, time, gc

from binascii import a2b_base64, hexlify
from hashlib import sha1

class server:

	def __init__(self, port = 80):

		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sock.bind(socket.getaddrinfo("0.0.0.0", port)[0][-1])
		self.sock.listen(25)

		self.poll = select.poll()
		self.poll.register(self.sock, select.POLLIN)

		self.sites = dict()

		try:
			with open('/etc/users.json', 'r') as f:
				self.users = json.load(f)
		except:
			self.users = dict()
		finally:
			gc.collect()

		try:
			with open('/etc/etags.json', 'r') as f:
				self.etags = json.load(f)
		except:
			self.etags = dict()
		finally:
			gc.collect()


	def accept(self, wait = 1000, timeout = 3):

		if self.poll.poll(wait):

			try: s = self.sock.accept()[0]
			except: return False
			else: s.settimeout(timeout)

			try: self.recv(s)
			except: return False
			finally: s.close()

			return True

	def head(self, sock, resp):

		sock.sendall(b'HTTP/1.1 ')
		sock.sendall(resp)
		sock.sendall(b'\r\n')

	def param(self, sock, key, value):

		sock.sendall(key)
		sock.sendall(b': ')
		sock.sendall(value)
		sock.sendall(b'\r\n')

	def error(self, sock, code):

		self.head(sock, code)
		self.param(sock, b'Connection', b'close')
		self.param(sock, b'WWW-Authenticate', b'Basic')
		sock.sendall(b'\r\n')

	def uncha(self, sock, etag):

		self.head(sock, b'304 Not Modified')
		self.param(sock, b'Connection', b'close')
		self.param(sock, b'Cache-Control', b'max-age=31536000')
		self.param(sock, b'ETag', etag)
		sock.sendall(b'\r\n')

	def recv(self, sock):

		buff = sock.recv(1460)
		stop = buff.find(b'\r\n\r\n')
		start = len(buff) - 3

		while stop == -1:

			if start < 0: start = 0

			old = len(buff)
			buff += sock.recv(1460)
			new = len(buff)

			if old == new: break

			stop = buff.find(b'\r\n\r\n', start)
			start = new - 3

		if stop == -1: raise ValueError('incomplete request')
		else: stop = stop + 2

		if not self.auth(buff, stop):
			code = b'401 Unauthorized'
			site = etag = None

		elif buff.startswith(b'GET /'):
			site, par, etag = self.get(sock, buff, stop)

		elif buff.startswith(b'POST /'):
			site, par = self.post(sock, buff, stop)
			etag = time.ticks_ms()

		else:
			code = b'405 Method Not Allowed'
			site = etag = None

		if site: code = self.resp(sock, site, par, etag)

		if code is not None: self.error(sock, code)

	def resp(self, sock, site, par, etag):

		if site in self.sites:
			try:
				res = str(self.sites[site](par)).encode()
				siz = len(res)
			except:
				return b'406 Not Acceptable'
			else:
				gen = True

		elif self.changed(site, etag):
			try:
				res, siz = self.site(site)
				etag = self.etags.get(site)
			except:
				return b'404 Not Found'
			else:
				gen = False

		else: return self.uncha(sock, etag)

		try: mim = self.mime(site)
		except: mim = b'text/plain'

		if site.endswith('.gz'): enc = b'gzip'
		else: enc = b'identity'

		if type(siz) == str: siz = siz.encode()
		else: siz = str(siz).encode()

		if gen or etag is None: cac = b'no-cache'
		else: cac = b'max-age=31536000'

		if etag is None: etag = str(time.ticks_ms()).encode()
		elif type(etag) == str: etag = etag.encode()
		else: etag = str(etag).encode()

		self.head(sock, b'200 OK')
		self.param(sock, b'Connection', b'close')
		self.param(sock, b'Content-Type', mim)
		self.param(sock, b'Content-Length', siz)
		self.param(sock, b'Content-Encoding', enc)
		self.param(sock, b'Cache-Control', cac)
		self.param(sock, b'ETag', etag)
		sock.sendall(b'\r\n')

		if gen: sock.sendall(res)
		else:

			chunk = bytearray(1460)
			view = memoryview(chunk)

			while True:

				try: n = res.readinto(view)
				except: break

				if n > 0: sock.sendall(view[:n])
				else: break

			res.close()

	def get(self, sock, req, stop):

		e = req.find(b'\r\n', 0, stop)
		a = req.find(b'GET /', 0, e) + 5
		b = req.find(b' HTTP', a, e)

		if a == 4 or b == -1 or a > b:
			raise ValueError('incomplete request')

		p = req.find(b'?', a, b)

		if p != -1:

			site = req[a:p]
			vlist = self.split(req[p+1:b])

		else:

			site = req[a:b]
			vlist = dict()

		a = req.find(b'If-None-Match: ', b + 11, stop) + 15
		b = req.find(b'\r\n', a, stop)

		if a == 14 or b == -1 or a > b: etag = None
		else: etag = req[a:b].decode()

		if site == b'': site = 'index.html'
		else: site = self.unquote(site).decode()

		return site, vlist, etag

	def post(self, sock, req, stop):

		e = req.find(b'\r\n', 0, stop)
		a = req.find(b'POST /', 0, e) + 6
		b = req.find(b' HTTP', a, e)

		if a == 5 or b == -1 or a > b:
			raise ValueError('incomplete request')

		if a == b: site = 'index.html'
		else: site = self.unquote(req[a:b]).decode()

		j = req.find(b'Content-Type: application/json', b, stop)
		p = req.find(b'Content-Type: text/plain', b, stop)
		a = req.find(b'Content-Length: ', b, stop) + 16
		b = req.find(b'\r\n', a, stop)

		if a == 15 or b == -1 or a > b:
			raise ValueError('incomplete request')

		size = int(req[a:b])
		req = req[stop + 2:]
		left = size - len(req)

		while left > 0:

			old = len(req)
			req += sock.recv(left)
			new = len(req)

			if old == new: break
			else: left = size - new

		if left > 0:
			raise ValueError('incomplete request')

		if j != -1: vlist = json.loads(req)
		elif p != -1: vlist = req.decode()
		else: vlist = self.split(req)

		return site, vlist

	def auth(self, req, stop):

		if not len(self.users): return True

		s = req.find(b'\r\n', 0, stop) + 2
		a = req.find(b'Authorization: Basic ', s, stop) + 21
		b = req.find(b'\r\n', a, stop)

		if a == 20 or b == -1 or a > b: return False
		else: auth = a2b_base64(req[a:b]).split(b':')

		if len(auth) != 2: return False
		else:
			u = auth[0].decode()
			p = auth[1]

		if u not in self.users: return False
		else:
			h = hexlify(sha1(p).digest())
			ok = self.users[u] == h.decode()

		return ok

	def unquote(self, string):

		if not string: return bytes()
		if b'%' not in string: return string

		bits = string.split(b'%')
		res = [ bits[0] ]

		for s in bits[1:]:

			try:

				char = bytes([int(s[:2], 16)])
				res.append(char)
				res.append(s[2:])

			except:

				res.append(b'%')
				res.append(s)

		return b''.join(res)

	def split(self, string):

		d = self.unquote
		vlist = dict()

		for p in string.split(b'&'):

			if p.find(b'=') != -1:

				i = p.split(b'=')
				k = d(i[0]).decode()
				v = d(i[1]).decode()

				vlist[k] = v

			else:

				k = d(p).decode()
				vlist[k] = None

		return vlist

	def site(self, path):

		if path == 'favicon.ico': path = '/obj/favicon.ico'

		elif path.endswith('.html'): path = '/http/%s' % path
		elif path.endswith('.json'): path = '/etc/%s' % path
		elif path.endswith('.css'): path = '/css/%s' % path
		elif path.endswith('.js'): path = '/src/%s' % path
		elif path.endswith('.gz'): path = '/arch/%s' % path

		else: path = '/var/%s' % path

		cont = open(path, 'rb')
		cont.seek(0, 2)
		size = cont.tell()
		cont.seek(0)

		return cont, size

	def mime(self, path):

		if path.endswith('.gz'): path = path[:-3]

		if path.startswith('/var/'): mime = b'application/json'
		elif path.endswith('.html'): mime = b'text/html'
		elif path.endswith('.json'): mime = b'application/json'
		elif path.endswith('.css'): mime = b'text/css'
		elif path.endswith('.ico'): mime = b'image/png'
		elif path.endswith('.js'): mime = b'text/javascript'

		else: mime = b'text/plain'

		return b'%s; charset=utf-8' % mime

	def changed(self, path, etag):

		return etag is None or etag != self.etags.get(path)

	def defsite(self, site, callback):

		self.sites[site] = callback
