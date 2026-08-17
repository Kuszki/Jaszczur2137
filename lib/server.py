# coding=UTF-8

import socket, select, json, time, gc

from binascii import a2b_base64, hexlify
from hashlib import sha1

class server:

	def __init__(self, port = 80):

		try: self.users = json.load(open('/etc/users.json', 'r'))
		except: self.users = dict()

		try: self.etags = json.load(open('/etc/etags.json', 'r'))
		except: self.etags = dict()

		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sock.bind(socket.getaddrinfo("0.0.0.0", port)[0][-1])
		self.sock.listen(25)

		self.poll = select.poll()
		self.poll.register(self.sock, select.POLLIN)

		self.sites = dict()

	def accept(self, wait = 1000):

		if self.poll.poll(wait):

			try: s = self.sock.accept()[0]
			except: return None
			else: s.settimeout(3)

			try: self.recv(s)
			except: gc.collect()
			else: gc.collect()
			finally: s.close()

	def recv(self, sock):

		try: buff = sock.recv(1460)
		except: return None

		while buff.find(b'\r\n\r\n') == -1:
			if not buff: raise BufferError
			else: buff += sock.recv(1460)

		if not self.auth(buff):
			code = b'401 Unauthorized'
			site = etag = None

		elif buff.startswith(b'GET /'):
			site, par, etag = self.get(buff, sock)

		elif buff.startswith(b'POST /'):
			site, par = self.post(buff, sock)
			etag = time.ticks_ms()

		else:
			code = b'405 Method Not Allowed'
			site = etag = None

		del buff; gc.collect()

		if site: code = self.resp(site, par, etag, sock)

		if etag == None:  etag = b'null'
		else: etag = str(etag).encode()

		if code: sock.sendall(\
			b'HTTP/1.1 %s\r\n' \
			b'ETag: %s\r\n'\
			b'Connection: close\r\n' \
			b'WWW-Authenticate: Basic\r\n' \
			b'\r\n' % (code, etag))

	def resp(self, site, par, etag, sock):

		if site in self.sites:
			try:
				res = str(self.sites[site](par)).encode()
				siz = len(res)
			except:
				return b'406 Not Acceptable'
			else:
				gen = True;

		elif self.changed(site, etag):
			try:
				res, siz = self.site(site)
				etag = self.etag(site)
			except:
				return b'404 Not Found'
			else:
				gen = False;

		else: return b'304 Not Modified'

		try: mim = self.mime(site)
		except: mim = b'text/plain'

		if site.endswith('.gz'): enc = b'gzip'
		else: enc = b'identity'

		if type(siz) == str: siz = siz.encode()
		else: siz = str(siz).encode()

		if type(etag) == str: etag = etag.encode()
		else: etag = str(etag).encode()

		try: sock.sendall(\
			b'HTTP/1.1 200 OK\r\n' \
			b'Connection: close\r\n' \
			b'Content-Type: %s\r\n' \
			b'Content-Length: %s\r\n' \
			b'Content-Encoding: %s\r\n' \
			b'ETag: %s\r\n' \
			b'\r\n' % (mim, siz, enc, etag))
		except:
			return b'500 Internal Server Error'

		if gen: sock.sendall(res)
		else:

			while True:

				chunk = res.read(1460)

				if not chunk: break
				else: sock.sendall(chunk)

			res.close()
			gc.collect()

	def get(self, req, sock):

		e = req.find(b'\r\n')
		a = req.find(b'GET /', 0, e) + 5
		b = req.find(b' HTTP', a, e)
		e = req.find(b'\r\n\r\n', b)

		if a == 4 or b == -1 or a > b:
			return str(), dict()

		p = req.find(b'?', a, b)

		if p != -1:

			site = self.unquote(req[a:p])
			vlist = self.split(req[p+1:b])

		else:

			site = self.unquote(req[a:b])
			vlist = dict()

		a = req.find(b'If-None-Match: ', b + 11, e) + 15
		b = req.find(b'\r\n', a, e)

		if a == 14 or b == -1 or a > b: etag = None
		else: etag = req[a:b].decode()

		if site == b'': site = 'index.html'
		else: site = site.decode()

		return site, vlist, etag

	def post(self, req, sock):

		e = req.find(b'\r\n')
		a = req.find(b'POST /', 0, e) + 6
		b = req.find(b' HTTP', a, e)
		e = req.find(b'\r\n\r\n', e)
		d = self.unquote

		if a == 5 or b == -1 or a > b:
			return str(), dict()

		elif a == b: site = 'index.html'
		else: site = d(req[a:b]).decode()

		j = req.find(b'Content-Type: application/json', b, e)
		p = req.find(b'Content-Type: text/plain', b, e)

		a = req.find(b'Content-Length: ', b, e) + 16
		b = req.find(b'\r\n', a, e)

		if a == 15 or b == -1 or a > b:
			return site, dict()

		else:
			try: leng = int(req[a:b])
			except: return site, dict()
			else: req = req[e+4:]

		while len(req) != leng:
			try: req += sock.recv(leng - len(req))
			except: return site, dict()
			if not req: raise BufferError

		if j != -1: vlist = json.loads(req)
		elif p != -1: vlist = req.decode()
		else: vlist = self.split(req)

		return site, vlist

	def auth(self, req):

		if not len(self.users): return True

		s = req.find(b'\r\n') + 2
		e = req.find(b'\r\n\r\n')
		a = req.find(b'Authorization: Basic ', s, e) + 21
		b = req.find(b'\r\n', a)

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

		if path.endswith(".gz"): path = path[:-3]

		if path.startswith('/var/'): mime = b'application/json'
		elif path.endswith('.html'): mime = b'text/html'
		elif path.endswith('.json'): mime = b'application/json'
		elif path.endswith('.css'): mime = b'text/css'
		elif path.endswith('.ico'): mime = b'image/png'
		elif path.endswith('.js'): mime = b'text/javascript'

		else: mime = b'text/plain'

		return b'%s; charset=utf-8' % mime

	def etag(self, path):

		if path in self.etags: return self.etags[path]
		else: return str(time.ticks_ms())

	def changed(self, path, etag):

		if etag == None: return True
		elif path not in self.etags: return True
		else: return etag != self.etags[path]

	def defsite(self, site, callback):

		self.sites[site] = callback

	def rmsite(self, site):

		del self.sites[site]
