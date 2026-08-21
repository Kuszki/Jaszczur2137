# coding=UTF-8

from micropython import const

import math

_INV = const(0); _INS = const(1);
_EXP = const(2); _UNV = const(3);
_UNF = const(4); _ERF = const(5);
_AGC = const(6); _OPE = const(7);
_UEN = const(8); _ZDV = const(9);

_NUM = const(0); _VAR = const(1);
_FUN = const(2); _END = const(3);

CONSTS = {

	"e": math.e,
	"pi": math.pi,
	"tau": math.tau,

	"inf": math.inf,
	"nan": math.nan,

	"true": True,
	"false": False,

	"null": None,

}

FUNCTS = {

	"abs": abs,
	"pow": pow,
	"min": min,
	"max": max,
	"round": round,

	"sqrt": math.sqrt,

	"mean": lambda *args: sum(args) / len(args),
	"floor": math.floor,
	"ceil": math.ceil,

	"sin": math.sin,
	"cos": math.cos,
	"tan": math.tan,

}

class nodus:

	def __init__(self, typ, row, col, val = None):

		self.typ = typ
		self.val = val
		self.chi = []

		self.row = row
		self.col = col

class script:

	def __init__(self, text, var = None, fun = None, mem = False):

		if mem: self.text = text
		else: self.text = str()

		if var is None: self.var = dict()
		else: self.var = var

		if fun is None: self.fun = dict()
		else: self.fun = fun

		self.ast = parse(analyze(text))
		self.mem = mem

	def __str__(self):

		return self.script()

	def update(self, text = None, var = None, fun = None, mem = None, check = True):

		if not (mem is None): self.mem = mem

		if text is not None: ast = parse(analyze(text))
		else: ast = self.ast

		if var is not None: cvar = var
		else: cvar = self.var

		if fun is not None: cfun = fun
		else: cfun = self.fun

		if check and checknode(ast, cvar, cfun): self.ast = ast
		elif not check: self.ast = ast
		else: return False

		if text is not None and self.mem: self.text = text
		if var is not None: self.var = var
		if fun is not None: self.fun = fun

		return True

	def compute(self):

		return compute(self.ast, self.var, self.fun)

	def script(self):

		return self.text

def analyze(text):

	toks = list()
	n = len(text)
	i = 0

	lin = 1;
	col = 1;
	com = False

	while i < n:

		c = text[i]

		if c == "#":

			com = True
			i += 1

			continue

		if c == "\n":

			com = False
			lin += 1
			col = 1
			i += 1

			continue

		elif com:

			i += 1

			continue

		if c <= " ":

			col += 1
			i += 1

			continue

		if c.isdigit():

			val = 0

			while i < n and text[i].isdigit():

				val = 10 * val + (ord(text[i]) - 48)

				col += 1
				i += 1

			if i < n and text[i] == ".":

				col += 1
				i += 1

				if i >= n or text[i] <= " ": raise ValueError(_INV, lin, col, { 'value': f'{val}.' })
				if not text[i].isdigit(): raise ValueError(_INV, lin, col, { 'value': f'{val}.{text[i]}'})

				mul = 0.1

				while i < n and text[i].isdigit():

					val = val + mul * (ord(text[i]) - 48)

					mul *= 0.1
					col += 1
					i += 1

				toks.append(nodus(_NUM, lin, col, val))

				continue

			if i < n and text[i] == ":":

				hh = val

				col += 1
				i += 1

				if i >= n or text[i] <= " ": raise ValueError(_INV, lin, col, { 'value': f'{hh}:' })
				if not text[i].isdigit(): raise ValueError(_INV, lin, col, { 'value': f'{hh}:{text[i]}' })

				mm = 0
				dig = 0

				while i < n and text[i].isdigit():

					mm = 10 * mm + (ord(text[i]) - 48)

					col += 1
					i += 1
					dig += 1

				if hh >= 24 or mm >= 60: raise ValueError(_INV, lin, col, { 'value': f'{hh}:{mm}' })
				if dig != 2: raise ValueError(_INV, lin, col, { 'value': f'{hh}:{mm}' })

				val = hh * 60 + mm

			toks.append(nodus(_NUM, lin, col, val))

			continue

		if c.isalpha() or c == "_":

			start = i
			i += 1
			col += 1

			while i < n:

				c = text[i]

				if c.isalpha() or c.isdigit() or c == "_":
					col += 1
					i += 1

				else: break

			name = text[start:i]

			if name == "in": toks.append(nodus(name, lin, col))
			elif name == "is": toks.append(nodus("==", lin, col))
			elif name == "not": toks.append(nodus("!", lin, col))
			elif name == "and": toks.append(nodus("&&", lin, col))
			elif name == "or": toks.append(nodus("||", lin, col))
			else: toks.append(nodus(_VAR, lin, col, name))

			continue

		if i + 1 < n:

			op = text[i : i + 2]

			if op in ("==", "!=", "<=", ">=", "&&", "||"):

				toks.append(nodus(op, lin, col))

				col += 2
				i += 2

				continue

		if c in "+-*/%^()<>!?:,":

			toks.append(nodus(c, lin, col))

			col += 1
			i += 1

			continue

		raise SyntaxError(_INS, lin, col, { 'value': c })

	toks.append(nodus(_END, lin, col))

	return toks

def parse(toks, pos = 0):

	def peek():
		return toks[pos]

	def take(expected = None):

		nonlocal pos
		tok = toks[pos]
		pos += 1

		if expected is not None and tok.typ != expected:
			raise SyntaxError(_EXP, tok.row, tok.col, { 'exp': expected, 'got': tok.typ, 'value': tok.val })

		return tok

	def expression():
		return conditional()

	def alternative():

		node = conjunction()

		while peek().typ == "||":
			op = take()
			op.chi = [node, conjunction()]
			node = op

		return node

	def conjunction():

		node = comparison()

		while peek().typ == "&&":
			op = take()
			op.chi = [node, comparison()]
			node = op

		return node

	def conditional():

		node = alternative()

		if peek().typ == "?":
			op = take()
			true_expr = expression()
			take(":")
			false_expr = conditional()
			op.chi = [node, true_expr, false_expr]
			node = op

		return node

	def comparison():

		left = addition()

		comparisons = []

		while peek().typ in ("==", "!=", "<", "<=", ">", ">=", "in"):

			if peek().typ == "in":

				op = take()

				take("(")

				op.chi.append(left)

				while True:

					op.chi.append(expression())

					if peek().typ != ",": break

					take(",")

				take(")")

				left = op

			else:

				op = take()
				right = addition()

				comparisons.append((op, left, right))

				left = right

		if not comparisons:	return left

		if len(comparisons) == 1:
			op, a, b = comparisons[0]
			op.chi = [a, b]

			return op

		first_op, a, b = comparisons[0]
		first_op.chi = [a, b]
		node = first_op

		for op, a, b in comparisons[1:]:
			op.chi = [a, b]

			and_node = nodus("&&", op.row, op.col)
			and_node.chi = [node, op]

			node = and_node

		return node

	def addition():

		node = multiplication()

		while peek().typ in ("+", "-"):
			op = take()
			op.chi = [node, multiplication()]
			node = op

		return node

	def multiplication():

		node = power()

		while peek().typ in ("*", "/", "%"):
			op = take()
			op.chi = [node, power()]
			node = op

		return node

	def power():

		node = unary()

		if peek().typ == "^":
			op = take()
			op.chi = [node, power()]
			node = op

		return node

	def unary():

		if peek().typ in ("!", "+", "-"):

			op = take()
			op.chi = [unary()]

			return op

		return primary()

	def primary():

		tok = peek()

		if tok.typ == _NUM: return take()

		if tok.typ == _VAR:

			ident = take()

			if peek().typ != "(": return ident

			args = []

			take("(")

			if peek().typ != ")":

				while True:

					args.append(expression())

					if peek().typ != ",": break
					else: take(",")

			take(")")

			call = nodus(_FUN, ident.row, ident.col, ident.val)
			call.chi = args

			return call

		if tok.typ == "(":

			take("(")
			node = expression()
			take(")")

			return node

		if tok.typ == ")":
			raise SyntaxError(_EXP, tok.row, tok.col, { 'got': tok.typ, 'exp': _NUM })

		raise SyntaxError(_UEN, tok.row, tok.col)

	tree = expression()
	take(_END)

	return tree

def compute(node, var = None, fun = None):

	if var is None: var = dict()
	if fun is None: fun = dict()

	if node.typ == _NUM: return node.val

	if node.typ == _VAR:

		if node.val in var: return var[node.val]
		if node.val in CONSTS: return CONSTS[node.val]

		raise NameError(_UNV, node.row, node.col, { 'value': node.val })

	if node.typ == _FUN:

		if node.val == "iif":

			if len(node.chi) != 3: raise TypeError(_AGC, node.row, node.col, { 'value': node.val })

			if compute(node.chi[0], var, fun): return compute(node.chi[1], var, fun)
			else: return compute(node.chi[2], var, fun)

		if node.val == "case":

			if len(node.chi) < 3 or len(node.chi) % 2 == 0: raise TypeError(_AGC, node.row, node.col, { 'value': node.val })

			for i in range(0, len(node.chi) - 1, 2):
				if compute(node.chi[i], var):
					return compute(node.chi[i + 1], var)

			return compute(node.chi[-1], var)

		try:
			args = [compute(arg, var, fun) for arg in node.chi]

			if node.val in fun: return fun[node.val](*args)
			if node.val in FUNCTS: return FUNCTS[node.val](*args)

		except Exception as e: raise RuntimeError(_ERF, node.row, node.col, { 'value': node.val, 'text': str(e) })

		raise NameError(_UNF, node.row, node.col, { 'value': node.val })

	if node.typ == "!": return not compute(node.chi[0], var, fun)

	if node.typ == "+" and len(node.chi) == 1: return compute(node.chi[0], var, fun)
	if node.typ == "-" and len(node.chi) == 1: return -compute(node.chi[0], var, fun)

	if node.typ == "?":
		if compute(node.chi[0], var, fun): return compute(node.chi[1], var, fun)
		else: return compute(node.chi[2], var, fun)

	if node.typ == "&&": return compute(node.chi[0], var, fun) and compute(node.chi[1], var, fun)
	if node.typ == "||": return compute(node.chi[0], var, fun) or compute(node.chi[1], var, fun)

	if node.typ == "in":

		value = compute(node.chi[0], var)

		for child in node.chi[1:]:
			if value == compute(child, var):
				return True

		return False

	a = compute(node.chi[0], var, fun)
	b = compute(node.chi[1], var, fun)

	try:

		if node.typ == "+": return a + b
		if node.typ == "-": return a - b
		if node.typ == "*": return a * b
		if node.typ == "/": return a / b
		if node.typ == "%": return a % b
		if node.typ == "^": return a ** b

		if node.typ == "==": return a == b
		if node.typ == "!=": return a != b
		if node.typ == "<": return a < b
		if node.typ == "<=": return a <= b
		if node.typ == ">": return a > b
		if node.typ == ">=": return a >= b

	except Exception as e:
		raise RuntimeError(_OPE, node.row, node.col, { 'text': str(e), 'a': a, 'b': b, 'op': node.typ })

	raise SyntaxError(_INS, node.row, node.col, { 'value': node.typ })

def validate(text, var = None, fun = None):

	if not isinstance(text, str): return False

	try: ast = parse(analyze(text))
	except Exception as e: return e

	try: return checknode(ast, var, fun)
	except Exception as e: return e

	return True

def checknode(node, var = None, fun = None):

	if node.typ == _VAR:
		if node.val not in CONSTS and (var is None or node.val not in var):
			raise NameError(_UNV, node.row, node.col, { 'value': node.val })

	if node.typ == _FUN and node.val not in ( "iif", "case" ):
		if node.val not in FUNCTS and (fun is None or node.val not in fun):
			raise NameError(_UNF, node.row, node.col, { 'value': node.val })

	if node.val == "iif":
		if len(node.chi) != 3:
			raise TypeError(_AGC, node.row, node.col, { 'value': node.val })

	if node.val == "case":
		if len(node.chi) < 3 or len(node.chi) % 2 == 0:
			raise TypeError(_AGC, node.row, node.col, { 'value': node.val })

	if len(node.chi) == 2 and(node.typ == "/" or node.typ == "%"):
		if node.chi[1].typ == _NUM and node.chi[1].val == 0:
			raise ZeroDivisionError(_ZDV, node.row, node.col)

	for n in node.chi: checknode(n, var, fun)

	return True

def genreport(text, var = None, fun = None):

	try: out = validate(text, var, fun)
	except: return False

	if isinstance(out, Exception): return out.args
	elif out is True: return True
	else: return False

try: from perror import message
except: message = lambda e: str(e)
