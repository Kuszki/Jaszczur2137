# coding=UTF-8

import math
import traceback

INV = 0; INS = 1; EXP = 2; UNV = 3; UNF = 4;
ERF = 5; AGC = 6; OPE = 7; UEN = 8; ZDV = 9;

NUM = 0; VAR = 1; FUN = 2; END = 3;

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

	def __init__(self, typ, row, col, value = None):

		self.typ = typ
		self.value = value
		self.children = []

		self.row = row
		self.col = col

class error(Exception):

	CODE = [
		"Nieprawidłowa wartość '{value}' przed linią {line}:{column}",
		"Nieprawidłowy symbol '{value}' przed linią {line}:{column}",
		"Oczekiwano {exps} natomiast napotkano {gots} przed linią {line}:{column}",
		"Niezdefiniowana zmienna '{value}' przed linią {line}:{column}",
		"Nieznana funkcja '{value}' przed linią {line}:{column}",
		"Błąd funkcji '{value}' o treści '{text}' przed linią {line}:{column}",
		"Nieprawidłowa liczba argumentów funkcji '{value}' przed linią {line}:{column}",
		"Błąd '{text}' podczas wykonywania operacji '{a} {op} {b}' przed linią {line}:{column}",
		"Nieoczekiwany koniec skryptu przed końcem wyrażenia po linii {line}:{column}",
		"Wymuszone dzielenie przez zero przed linią {line}:{column}",
	]

	EXPS = {
		NUM: "wyrażenia",
		VAR: "zmiennej",
		FUN: "funkcji",
		END: "końca skryptu",
	}

	GOTS = {
		NUM: "wartość '%s'",
		VAR: "zmienną '%s'",
		FUN: "funkcję '%s'",
		END: "koniec skryptu",
	}

	UNKCODE = "Napotkano nieznany błąd"

	def __init__(self, err, line, column, **params):

		if 'exp' in params:
			if params['exp'] in self.EXPS.keys():
				es = self.EXPS[params['exp']]
			else:
				es = "'%s'" % params['exp']
		else: es = None

		if 'got' in params:
			if params['got'] in (NUM, VAR, FUN):
				gs = self.GOTS[params['got']] % params['value']
			elif params['got'] == END:
				gs = self.GOTS[params['got']]
			else:
				gs = "'%s'" % params['got']
		else: gs = None

		self.params = params
		params['code'] = err
		params['line'] = line
		params['column'] = column

		if err >= len(self.CODE): params['str'] = self.UNKCODE
		else: params['str'] = self.CODE[err].format(**params, gots = gs, exps = es)

		super().__init__(params)

	def __str__(self): return self.params['str']

	def dump(self): return self.params

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

	tokens = list()
	n = len(text)
	i = 0

	line = 1;
	column = 0;
	comment = False

	while i < n:

		c = text[i]

		if c == "#":

			comment = True
			i += 1

			continue

		if c == "\n":

			comment = False
			line += 1
			column = 0
			i += 1

			continue

		elif comment:

			i += 1

			continue

		if c <= " ":

			column += 1
			i += 1

			continue

		if c.isdigit():

			value = 0

			while i < n and text[i].isdigit():

				value = 10 * value + (ord(text[i]) - 48)

				column += 1
				i += 1

			if i < n and text[i] == ".":

				column += 1
				i += 1

				if i >= n or text[i] <= " ": raise error(INV, line, column, value = f"{value}.")
				if not text[i].isdigit(): raise error(INV, line, column, value = f"{value}.{text[i]}")

				mul = 0.1

				while i < n and text[i].isdigit():

					value = value + mul * (ord(text[i]) - 48)

					mul *= 0.1
					column += 1
					i += 1

				tokens.append(nodus(NUM, line, column, value))

				continue

			if i < n and text[i] == ":":

				hours = value

				column += 1
				i += 1

				if i >= n or text[i] <= " ": raise error(INV, line, column, value = f"{hours}:")
				if not text[i].isdigit(): raise error(INV, line, column, value = f"{hours}:{text[i]}")

				minutes = 0
				digits = 0

				while i < n and text[i].isdigit():

					minutes = 10 * minutes + (ord(text[i]) - 48)

					column += 1
					i += 1
					digits += 1

				if hours >= 24 or minutes >= 60: raise error(INV, line, column, value = f"{hours}:{minutes:02d}")
				if digits != 2: raise error(INV, line, column, value = f"{hours}:{minutes}")

				value = hours * 60 + minutes

			tokens.append(nodus(NUM, line, column, value))

			continue

		if c.isalpha() or c == "_":

			start = i
			i += 1
			column += 1

			while i < n:

				c = text[i]

				if c.isalpha() or c.isdigit() or c == "_":
					column += 1
					i += 1

				else: break

			name = text[start:i]

			if name == "in": tokens.append(nodus(name, line, column))
			elif name == "not": tokens.append(nodus("!", line, column))
			elif name == "and": tokens.append(nodus("&&", line, column))
			elif name == "or": tokens.append(nodus("||", line, column))
			else: tokens.append(nodus(VAR, line, column, name))

			continue

		if i + 1 < n:

			op = text[i : i + 2]

			if op in ("==", "!=", "<=", ">=", "&&", "||"):

				tokens.append(nodus(op, line, column))

				column += 2
				i += 2

				continue

		if c in "+-*/%^()<>!?:,":

			tokens.append(nodus(c, line, column))

			column += 1
			i += 1

			continue

		raise error(INS, line, column, value = c)

	tokens.append(nodus(END, line, column))

	return tokens

def parse(tokens, pos = 0):

	def peek():
		return tokens[pos]

	def take(expected = None):

		nonlocal pos
		token = tokens[pos]
		pos += 1

		if expected is not None and token.typ != expected:
			raise error(EXP, token.row, token.col, exp = expected, got = token.typ, value = token.value)

		return token

	def expression():
		return conditional()

	def alternative():

		node = conjunction()

		while peek().typ == "||":
			op = take()
			op.children = [node, conjunction()]
			node = op

		return node

	def conjunction():

		node = comparison()

		while peek().typ == "&&":
			op = take()
			op.children = [node, comparison()]
			node = op

		return node

	def conditional():

		node = alternative()

		if peek().typ == "?":
			op = take()
			true_expr = expression()
			take(":")
			false_expr = conditional()
			op.children = [node, true_expr, false_expr]
			node = op

		return node

	def comparison():

		left = addition()

		comparisons = []

		while peek().typ in ("==", "!=", "<", "<=", ">", ">=", "in"):

			if peek().typ == "in":

				op = take()

				take("(")

				op.children.append(left)

				while True:

					op.children.append(expression())

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
			op.children = [a, b]

			return op

		first_op, a, b = comparisons[0]
		first_op.children = [a, b]
		node = first_op

		for op, a, b in comparisons[1:]:
			op.children = [a, b]

			and_node = nodus("&&", op.row, op.col)
			and_node.children = [node, op]

			node = and_node

		return node

	def addition():

		node = multiplication()

		while peek().typ in ("+", "-"):
			op = take()
			op.children = [node, multiplication()]
			node = op

		return node

	def multiplication():

		node = power()

		while peek().typ in ("*", "/", "%"):
			op = take()
			op.children = [node, power()]
			node = op

		return node

	def power():

		node = unary()

		if peek().typ == "^":
			op = take()
			op.children = [node, power()]
			node = op

		return node

	def unary():

		if peek().typ in ("!", "+", "-"):

			op = take()
			op.children = [unary()]

			return op

		return primary()

	def primary():

		token = peek()

		if token.typ == NUM: return take()

		if token.typ == VAR:

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

			call = nodus(FUN, ident.row, ident.col, ident.value)
			call.children = args

			return call

		if token.typ == "(":

			take("(")
			node = expression()
			take(")")

			return node

		if token.typ == ")":
			raise error(EXP, token.row, token.col, got = token.typ, exp = NUM)

		raise error(UEN, token.row, token.col)

	tree = expression()
	take(END)

	return tree

def compute(node, var = None, fun = None):

	if var is None: var = dict()
	if fun is None: fun = dict()

	if node.typ == NUM: return node.value

	if node.typ == VAR:

		if node.value in var: return var[node.value]
		if node.value in CONSTS: return CONSTS[node.value]

		raise error(UNV, node.row, node.col, value = node.value)

	if node.typ == FUN:

		if node.value == "iif":

			if len(node.children) != 3: raise error(AGC, node.row, node.col, value = node.value)

			if compute(node.children[0], var, fun): return compute(node.children[1], var, fun)
			else: return compute(node.children[2], var, fun)

		if node.value == "case":

			if len(node.children) < 3 or len(node.children) % 2 == 0: raise error(AGC, node.row, node.col, value = node.value)

			for i in range(0, len(node.children) - 1, 2):
				if compute(node.children[i], var):
					return compute(node.children[i + 1], var)

			return compute(node.children[-1], var)

		try:
			args = [compute(arg, var, fun) for arg in node.children]

			if node.value in fun: return fun[node.value](*args)
			if node.value in FUNCTS: return FUNCTS[node.value](*args)

		except Exception as e: raise error(ERF, node.row, node.col, value = node.value, text = str(e))

		raise error(UNF, node.row, node.col, value = node.value)

	if node.typ == "!": return not compute(node.children[0], var, fun)

	if node.typ == "+" and len(node.children) == 1: return compute(node.children[0], var, fun)
	if node.typ == "-" and len(node.children) == 1: return -compute(node.children[0], var, fun)

	if node.typ == "?":
		if compute(node.children[0], var, fun): return compute(node.children[1], var, fun)
		else: return compute(node.children[2], var, fun)

	if node.typ == "&&": return compute(node.children[0], var, fun) and compute(node.children[1], var, fun)
	if node.typ == "||": return compute(node.children[0], var, fun) or compute(node.children[1], var, fun)

	if node.typ == "in":

		value = compute(node.children[0], var)

		for child in node.children[1:]:
			if value == compute(child, var):
				return True

		return False

	a = compute(node.children[0], var, fun)
	b = compute(node.children[1], var, fun)

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
		raise error(OPE, node.row, node.col, text = str(e), a = a, b = b, op = node.typ)

	raise error(INS, node.row, node.col, value = node.typ)

def validate(text, var = None, fun = None):

	if not isinstance(text, str): return False

	try: ast = parse(analyze(text))
	except Exception as e: return e

	try: return checknode(ast, var, fun)
	except Exception as e: return e

	return True

def checknode(node, var = None, fun = None):

	if node.typ == VAR:
		if node.value not in CONSTS and (var is None or node.value not in var):
			raise error(UNV, node.row, node.col, value = node.value)

	if node.typ == FUN and node.value not in ( "iif", "case" ):
		if node.value not in FUNCTS and (fun is None or node.value not in fun):
			raise error(UNF, node.row, node.col, value = node.value)

	if node.value == "iif":
		if len(node.children) != 3:
			raise error(AGC, node.row, node.col, value = node.value)

	if node.value == "case":
		if len(node.children) < 3 or len(node.children) % 2 == 0:
			raise error(AGC, node.row, node.col, value = node.value)

	if len(node.children) == 2 and(node.typ == "/" or node.typ == "%"):
		if node.children[1].typ == NUM and node.children[1].value == 0:
			raise error(ZDV, node.row, node.col)

	for n in node.children: checknode(n, var, fun)

	return True

def genreport(text, var = None, fun = None):

	try: out = validate(text, var, fun)
	except: return False

	if isinstance(out, Exception): return out.args
	elif out is True: return True
	else: return False
