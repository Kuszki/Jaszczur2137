const CODE =
[
	"Nieprawidłowa wartość '{value}' przed linią {line}:{column}",
	"Nieprawidłowy symbol '{value}' przed linią {line}:{column}",
	"Oczekiwano {exps} natomiast napotkano {gots} przed linią {line}:{column}",
	"Niezdefiniowana zmienna '{value}' przed linią {line}:{column}",
	"Nieznana funkcja '{value}' przed linią {line}:{column}",
	"Błąd funkcji '{value}' o treści '{text}' przed linią {line}:{column}",
	"Nieprawidłowa liczba argumentów funkcji '{value}' przed linią {line}:{column}",
	"Błąd '{text}' podczas wykonywania operacji '{a} {op} {b}' przed linią {line}:{column}",
	"Nieoczekiwany koniec skryptu przed końcem wyrażenia po linii {line}:{column}",
	"Wymuszone dzielenie przez zero przed linią {line}:{column}"
];

const EXPS =
{
	0: "wyrażenia",
	1: "zmiennej",
	2: "funkcji",
	3: "końca skryptu"
};

const GOTS =
{
	0: "wartość '{value}'",
	1: "zmienną '{value}'",
	2: "funkcję '{value}'",
	3: "koniec skryptu"
};

const UNKCODE = "Napotkano nieznany błąd";

function trException(e)
{
	if (e.length < 3) return UNKCODE;

	let par = e.length > 3 ? e[3] : {};

	par.code = e[0];
	par.line = e[1];
	par.column = e[2];

	if (par.code >= CODE.length) return UNKCODE;
	else e = par;

	let exps = null;
	let gots = null;

	if ("exp" in e) exps = e.exp in EXPS ? EXPS[e.exp] : `'${e.exp}'`;

	if ("got" in e)
	{
		if (e.got >= 0 && e.got <= 2)
		{
			gots = GOTS[e.got].replace("{value}", e.value);
		}
		else if (e.got === 3)
		{
			gots = GOTS[e.got];
		}
		else
		{
			gots = `'${e.got}'`;
		}
	}

	const params = { ...e, exps, gots };

	return CODE[e.code].replace(/\{(\w+)\}/g, (_, key) =>
	{
		return params[key] ?? `{${key}}`;
	});
}
