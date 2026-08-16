const pl_colors = ['firebrick', 'olive', 'teal', 'seagreen', 'coral', 'crimson', 'limegreen', 'peru'];

const errors =
{
	'pwr': 'Nie udało się wykonać zapytania'
};

const dones =
{
	'pwr': 'Sterowanie zostało zaktualizowane'
};

let unit_list = [];

function onLoad()
{
	$.ajaxSetup({ 'timeout': 5000 });

	$.when
	(
		$.getJSON('plot.json'),
		$.getJSON('history.json')
	)
	.done(function(config, hist)
	{
		let off = Date.UTC(2000, 0, 1);
		let data = new Array();
		let conf = config[0];

		conf.options.tooltips.callbacks.label = function(tooltipItem, data) {
			return Number(tooltipItem.yLabel).toFixed(1);
		};

		moment.locale('pl');

		let ctx = $('#plot')[0].getContext('2d');
		let plot = new Chart(ctx, conf);

		for (k in hist[0]) $.getJSON(hist[0][k], function(x)
		{
			let cn = plot.data.datasets.length;
			let hash = genHash(x.unit);

			if (!unit_list.includes(hash))
			{
				unit_list.push(hash);

				plot.options.scales.yAxes.push({
					id: hash,
					position: unit_list.length % 2 ? 'right' : 'left'
				});
			}

			x.fill = false;
			x.borderColor = pl_colors[cn];
			x.cubicInterpolationMode = 'monotone';
			x.yAxisID = hash;

			for (j = 0; j < x.data.length; ++j)
			{
				const old = x.data[j]['t'] * 1000;
				const t = new Date(old + off);

				if (plot.options.pan.rangeMax.x == null)
				{
					plot.options.zoom.rangeMax.x = t;
					plot.options.pan.rangeMax.x = t;
				}

				if (plot.options.pan.rangeMin.x == null)
				{
					plot.options.zoom.rangeMin.x = t;
					plot.options.pan.rangeMin.x = t;
				}

				if (plot.options.pan.rangeMax.x < t)
				{
					plot.options.zoom.rangeMax.x = t;
					plot.options.pan.rangeMax.x = t;
				}

				if (plot.options.pan.rangeMin.x > t)
				{
					plot.options.zoom.rangeMin.x = t;
					plot.options.pan.rangeMin.x = t;
				}

				x.data[j]['t'] = t;
			}

			plot.data.datasets.push(x);
			plot.update();
		});
	})
	.fail(function()
	{
		$('#graph').html('<center>Brak danych do załadowania</center>');
	});

	$.getJSON('sensors.json', onSensors)
	.done(function()
	{
		setInterval($.getJSON, 30000, 'sensors.json', onSensors);
	})
	.fail(function()
	{
		$('#sensors').html('Błąd w ładowaniu danych');
	});

	$.getJSON('outputs.json', onOutputs)
	.done(function()
	{
		setInterval($.getJSON, 30000, 'outputs.json', onOutputs);
	})
	.fail(function()
	{
		$('#outputs').html('Błąd w ładowaniu danych');
	});
}

function onSensors(data)
{
	const container = document.getElementById("sensors");
	const table = document.createElement("table");

	let tr = document.createElement("tr");

	let th = document.createElement("th");
	th.textContent = "Wielkość";
	tr.appendChild(th);

	th = document.createElement("th");
	th.textContent = "Wartość";
	tr.appendChild(th);

	table.appendChild(tr);

	const keys = Object.keys(data).sort(function(a, b)
	{
		if (data[a].name < data[b].name) return -1;
		if (data[a].name > data[b].name) return 1;
		return 0;
	});

	for (const k in keys)
	{
		const sensor = data[keys[k]];
		const tr = document.createElement("tr");

		genCell(tr, sensor.name);
		genCell(tr, sensor.text);

		table.appendChild(tr);
	}

	container.replaceChildren(table);
}

function onOutputs(data)
{
	const container = document.getElementById("outputs");
	const table = document.createElement("table");

	let tr = document.createElement("tr");

	let th = document.createElement("th");
	th.textContent = "Wyjście";
	tr.appendChild(th);

	th = document.createElement("th");
	th.textContent = "Sterowanie";
	tr.appendChild(th);

	th = document.createElement("th");
	th.textContent = "Akcje";
	tr.appendChild(th);

	table.appendChild(tr);

	const keys = Object.keys(data);
	for (const k in keys)
	{
		const output = data[keys[k]];
		const tr = document.createElement("tr");
		const hrefs = [];

		genCell(tr, output.name);
		genCell(tr, `${output.status ? "ON" : "OFF"} (${output.driver ? "A" : "M"})`);

		for (let i = 0; i < 3; ++i)
		{
			hrefs[i] = document.createElement("a");
			hrefs[i].href = "javascript:void(0)";
		}

		hrefs[0].title = "Włącz";
		hrefs[0].onclick = function() { onEnable(output.uid, 1); };
		hrefs[0].textContent = "⏻";

		hrefs[1].title = "Wyłącz";
		hrefs[1].onclick = function() { onEnable(output.uid, 0); };
		hrefs[1].textContent = "⏼";

		hrefs[2].title = "Włącz";
		hrefs[2].onclick = function() { onDriver(output.uid, 1); };
		hrefs[2].textContent = "⚙";

		genCell(tr, hrefs);

		table.appendChild(tr);
	}

	container.replaceChildren(table);
}

function onEnable(id, param)
{
	if (set_locked) return;
	else set_locked = true;

	showToast('Łączenie z urządzeniem...', 0);

	$.get('power', { uid: id, power: param })
	.done(function()
	{
		$.getJSON('outputs.json', onOutputs);
		onDone('pwr');
	})
	.fail(function()
	{
		onError('pwr');
	});
}

function onDriver(id, param)
{
	if (set_locked) return;
	else set_locked = true;

	showToast('Łączenie z urządzeniem...', 0);

	$.get('driver', { uid: id, driver: param })
	.done(function()
	{
		$.getJSON('outputs.json', onOutputs);
		onDone('pwr');
	})
	.fail(function()
	{
		onError('pwr');
	});
}
