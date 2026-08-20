const messages =
{
	'pwr':
	{
		0: 'Wyłączono',
		1: 'Włączono',
		'all': ' wszystkie wyjścia',
		'one': ' wyjście '
	},
	'drv':
	{
		0: 'Ustawiono sterowanie ręczne',
		1: 'Ustawiono sterowanie automatyczne',
		'all': ' dla wszystkich wyjść',
		'one': ' dla wyjścia '
	},
	'boot':
	{
		1: 'Włączono sterownik',
		2: 'Zrestartowano sterownik',
		3: 'Awaria sterownika',
		4: 'Obudzono sterownik',
		5: 'Zrestartowano sterownik'
	},
	'err': 'Błąd podczas wykonywania skryptu dla zmiennej ',
}

const errors =
{
	'clr': 'Nie udało się usunąć historii',
	'msg': 'Nieznany zapis dziennika',
};

let firstload = true;

function onLoad()
{
	$.ajaxSetup({ 'timeout': 5000 });

	$.getJSON('logs.json', onLogs)
	.done(function()
	{
		setInterval($.getJSON, 60000, 'logs.json', onLogs);
	})
	.fail(function()
	{
		$('#log').html('<p>Brak danych do załadowania</p>');
	});
}

function onLogs(data)
{
	const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };

	const off = Date.UTC(2000, 0, 1);

	const container = document.getElementById("log");
	const table = document.createElement("table");

	let num = 0, found = false, days = {};

	data.sort(function(a, b)
	{
		if (a.t > b.t) return -1;
		if (a.t < b.t) return 1;
		return 0;
	});

	for (const k in data)
	{
		const date = new Date(data[k].t * 1000 + off);
		const sdate = date.toLocaleDateString('pl', options);

		if (days.hasOwnProperty(sdate))
		{
			days[sdate].push(data[k]);
		}
		else
		{
			days[sdate] = [ data[k] ];
		}
	}

	for (const k in days)
	{
		const hs = genHash(k).toString();

		if (!firstload || !num) ++num;
		else { hidden.push(hs); ++num; }

		const hd = hidden.indexOf(hs) == -1 ? "on" : "hide";
		const uk = k.charAt(0).toUpperCase() + k.slice(1);

		let header = document.createElement("p");
		header.textContent = uk;
		header.onclick = function() { onExpand(hs); };

		let child = document.createElement("table");
		child.className = hd;
		child.id = hs;

		table.appendChild(header);
		table.appendChild(child);

		for (const j in days[k])
		{
			const item = days[k][j];
			let msg = new String()

			const time = new Date(item.t * 1000 + off);
			const sdate = time.toLocaleTimeString('pl');

			if (item.k == 'err') msg = messages['err'] + item.u;
			else if (item.u == null) msg = messages[item.k][item.s];
			else if (item.u == 'all') msg = messages[item.k][item.s] + messages[item.k]['all'];
			else msg = messages[item.k][item.s] + messages[item.k]['one'] + item.u;

			if (msg == null) msg = errors['msg'];

			const tr = document.createElement("tr");

			if (item.k == 'err') tr.title = trException(item.s);

			genCell(tr, sdate);
			genCell(tr, msg);

			child.appendChild(tr);
		}
	}

	container.replaceChildren(table);

	firstload = false;
}

function onSave()
{
	let f = document.getElementById('log');
	let txt = f.textContent;

	let uriContent = 'data:text/plain;charset=utf-8,' + encodeURIComponent(txt);
	let newWindow = window.open(uriContent, 'k-esp-ctrl-log.txt');
}

function onClear()
{
	if (set_locked) return;
	else set_locked = true;

	$.when($.get('config', { 'rmlogs': true }))
	.done(function(msg)
	{
		if (msg != "True") { onError(); return; }

		$('#log').html('<table></table>');
		showToast('Usunięto historię zdarzeń', 5000);

		set_locked = false;
	})
	.fail(function()
	{
		onError('clr');
	});
}
