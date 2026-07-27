function onLoad()
{
	$.ajaxSetup({ 'timeout': 5000 });

	$.getJSON('devinfo.json', onDevinfo)
	.done(function()
	{
		setInterval($.getJSON, 30000, 'devinfo.json', onDevinfo);
	})
	.fail(function()
	{
		$('#dev').html('Błąd w ładowaniu danych');
	});

	$.getJSON('timing.json', onTimes)
	.done(function()
	{
		setInterval($.getJSON, 90000, 'timing.json', onTimes);
	})
	.fail(function()
	{
		$('#raw').html('Błąd w ładowaniu danych');
	});
}

function onDevinfo(data)
{
	onDatatab(data, 'dev');
}

function onTimes(data)
{
	onTimetab(data, 'syn');
}

function onSave()
{
	let f = document.getElementById('informations');
	let txt = f.textContent;

	let uriContent = 'data:text/plain;charset=utf-8,' + encodeURIComponent(txt);
	let newWindow = window.open(uriContent, 'k-esp-ctrl-info.txt');
}

function onTimetab(data, parrent)
{
	const container = document.getElementById(parrent);
	const table = document.createElement("table");

	const off = Date.UTC(2000, 0, 1);

	const keys = Object.keys(data).sort();
	for (const k in keys)
	{
		let temp = data[keys[k]];

		const time = new Date(temp * 1000 + off);
		const sdate = time.toLocaleString('pl');
		const v = temp != 0 ? sdate : '-'.repeat(32);

		const tr = document.createElement("tr");

		genCell(tr, keys[k]);
		genCell(tr, v);

		table.appendChild(tr);
	}

	container.replaceChildren(table);
}

function onDatatab(data, parrent)
{
	const container = document.getElementById(parrent);
	const table = document.createElement("table");

	const off = Date.UTC(2000, 0, 1);

	const keys = Object.keys(data).sort();
	for (const i in keys)
	{
		const k = keys[i];

		if (data[k] != null) temp = data[k].toString();
		else temp = 'Brak danych';

		const p = k.charAt(0).toUpperCase() + k.slice(1);
		const v = temp.charAt(0).toUpperCase() + temp.slice(1);

		const tr = document.createElement("tr");

		genCell(tr, p);
		genCell(tr, v);

		table.appendChild(tr);
	}

	container.replaceChildren(table);
}
