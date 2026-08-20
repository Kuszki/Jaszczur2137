# coding=UTF-8

from micropython import const

_INV = const(0); _INS = const(1);
_EXP = const(2); _UNV = const(3);
_UNF = const(4); _ERF = const(5);
_AGC = const(6); _OPE = const(7);
_UEN = const(8); _ZDV = const(9);

_NUM = const(0); _VAR = const(1);
_FUN = const(2); _END = const(3);

_CODE = [
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

_EXPS = {
	_NUM: "wyrażenia",
	_VAR: "zmiennej",
	_FUN: "funkcji",
	_END: "końca skryptu",
}

_GOTS = {
	_NUM: "wartość '%s'",
	_VAR: "zmienną '%s'",
	_FUN: "funkcję '%s'",
	_END: "koniec skryptu",
}

_UNKCODE = const("Napotkano nieznany błąd")

def message(e):

	if not issubclass(type(e), Exception): return None
	elif len(e.args) < 3: return _UNKCODE
	else: 
	
		err = e.args[0]
		params = e.args[3] if len(e.args) > 3 else dict()
		
		params['line'] = e.args[1]
		params['column']= e.args[2]
	
	if err >= len(_CODE): params['str'] = _UNKCODE

	if 'exp' in params:
		if params['exp'] in _EXPS.keys():
			es = _EXPS[params['exp']]
		else:
			es = "'%s'" % params['exp']
	else: es = None

	if 'got' in params:
		if params['got'] in (_NUM, _VAR, _FUN):
			gs = _GOTS[params['got']] % params['value']
		elif params['got'] == _END:
			gs = _GOTS[params['got']]
		else:
			gs = "'%s'" % params['got']
	else: gs = None
	
	return _CODE[err].format(**params, gots = gs, exps = es)
