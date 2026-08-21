CodeMirror.defineMode("script", function()
{

	const keywords =
	{
		"in": true,
		"is": true,
		"not": true,
		"and": true,
		"or": true,
		"iif": true,
		"case": true
	};

	const constants =
	{
		"e": true,
		"pi": true,
		"tau": true,
		"inf": true,
		"nan": true,
		"true": true,
		"false": true,
		"null": true
	};

	const functions =
	{
		"abs": true,
		"pow": true,
		"min": true,
		"max": true,
		"round": true,

		"sqrt": true,
		"floor": true,
		"ceil": true,

		"sin": true,
		"cos": true,
		"tan": true,

		"mean": true,
		"clamp": true
	};


	return {
		token: function(stream, state)
		{
			if (stream.eatSpace()) return null;

			if (stream.peek() === "#")
			{
				stream.skipToEnd();
				return "comment";
			}

			if (stream.match(/^\d+([:\.]\d+)?/)) return "number";

			if (stream.match(/^[A-Za-z_][A-Za-z0-9_]*/))
			{

				let word = stream.current();

				if (keywords[word]) return "keyword";
				if (constants[word]) return "atom";
				if (functions[word]) return "def";

				return "variable";
			}

			if (stream.match(/^(==|!=|<=|>=|&&|\|\|)/)) return "operator";
			if (stream.match(/^[+\-*/%^<>!?:,]/)) return "operator";
			if (stream.match(/^[()]/)) return "bracket";

			stream.next();

			return null;
		}
	};
});
