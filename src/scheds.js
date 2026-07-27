const errors =
{
	'load': 'Nie udało się wczytać harmonogramu',
	'save': 'Nie udało się zapisać harmonogramu',
	'check': 'Wykryto błędy w skryptach',
	'nojob': 'Brak zmian w skryptach',
	'empty': 'Wykryto puste skrypty',
	'nc': 'Brak zmian do zapisania'
};

const dones =
{
	'save': 'Harmonogram został zapisany',
	'check': 'Wszystkie skrypty są poprawne'
};

const variables =
{
	't': 'Czas',
	'h': 'Godzina',
	'm': 'Minuta',
	'day': 'Dzień',
	'mon': 'Miesiąc',
	'year': 'Rok',
	'wday': 'Dzień tygodnia',
};

const off = 2*Date.UTC(2000, 0, 1) - new Date(2000, 0, 1);

let checks = 0, good = 0, bad = 0;
let sh_org = null, sh_last = null;
let uids = {}, edits = {};

function onLoad()
{
	$.ajaxSetup({ 'timeout': 5000 });

	$.when
	(
		$.getJSON('sensors.json'),
		$.getJSON('outputs.json'),
	)
	.done(function(sensors, outputs)
	{
		sh_org = structuredClone(outputs[0]);
		sh_last = structuredClone(outputs[0]);

		onTopicadd("Zmienne");
		onHelpbatch(variables);

		onTopicadd("Wielkości");
		onSensors(sensors[0]);

		onTopicadd("Wyjścia");
		onScheds(outputs[0]);
	})
	.fail(function()
	{
		onError('load');
	});
}

function onScheds(data)
{
	let keys = Object.keys(data);

	for (const k in Object.keys(data))
	{
		onAppend(keys[k], data[keys[k]]);
		uids[keys[k]] = data[keys[k]].uid;
	}
}

function onSensors(data)
{
	let keys = Object.keys(data).sort(function(a, b)
	{
		if (data[a].uid < data[b].uid) return -1;
		if (data[a].uid > data[b].uid) return 1;
		return 0;
	});

	for (const k in keys) onHelpadd(data[keys[k]].uid, data[keys[k]].name)
}

function onAppend(id, data)
{
	let sec = document.getElementById('scheds');
	let form = document.createElement('form');
	let tab = document.createElement('table');
	let row = document.createElement('tr');

	let sid = '[' + id + ']';

	let cols = []; for (i = 0; i < 2; ++i)
	{
		col = document.createElement('td');
		row.appendChild(col);
		cols.push(col);
	}

	let lab = genLabel(form, data['uid'], null, 'slab' + sid);
	let code = genItem(form, 'textarea', '', 'sedit' + sid);

	onHelpadd(data['uid'], data['name']);

	lab.textContent = data['name'];
	code.value = data['code'];

	cols[0].appendChild(lab);
	cols[1].appendChild(code);

	tab.appendChild(row);
	form.appendChild(tab);
	sec.appendChild(form);

	edits[id] = CodeMirror.fromTextArea(code,
	{
		mode: "script",
		indentUnit: 5,
		lineNumbers: true,
		lineWrapping: true,
		styleActiveLine: true,
		gutters: [ "errors" ]
	});

	form.id = 'sched_' + id;
}

function onSave()
{
	if (set_locked) return;
	else set_locked = true;

	let sec = document.getElementById('scheds').children;
	let cha = {}, req = {}, ch = false, ok = true;

	for (i = 0; i < sec.length; ++i)
	{
		let id = sec[i].id.replace('sched_', '');
		let sid = '[' + id + ']';
		let org = sh_last[id];

		let elab = document.getElementById('slab' + sid);
		let ecode = document.getElementById('scode' + sid);
		let code = edits[id].getValue();

		if (org['code'] != code)
		{
			req[uids[id]] = code;
			cha[id] = org;
			cha[id]['code'] = code;
			ch = true;
		}
		if (code.trim() === "")
		{
			edits[id].getWrapperElement().classList.add("error");
			edits[id].clearGutter("errors");
			elab.title = "Skrypt jest pusty";
			ok = false;
		}
	}

	if (ch && ok) showToast('Zapisywanie zmian...', 0);

	if (!ch) onError('nc');
	else if (!ok) onError('empty');
	else $.ajax(
	{
		'url': 'codeup',
		'type': 'POST',
		'contentType': 'application/json',
		'data': JSON.stringify(req)
	})
	.done(function(msg)
	{
		if (msg == "True")
		{
			onUpdate(cha);
			onDone('save');
		}
		else
		{
			onError('save');
		}
	})
	.fail(function()
	{
		onError('save');
	});
}

function onCheck()
{
	let sec = document.getElementById('scheds').children;

	if (set_locked) return;
	else
	{
		set_locked = true;
		checks = sec.length;
		requested = checks;
	}

	showToast('Weryfikacja skryptów...', 0);

	for (i = 0; i < sec.length; ++i)
	{
		let id = sec[i].id.replace('sched_', '');
		let sid = '[' + id + ']';
		let org = sh_last[id];

		let elab = document.getElementById('slab' + sid);
		let code = edits[id].getValue();

		if (code == org.code)
		{
			requested--;
			checks--;

			onCkecked();
		}
		else if (code.trim() === "")
		{
			edits[id].getWrapperElement().classList.add("error");
			edits[id].clearGutter("errors");
			elab.title = "Skrypt jest pusty";
			bad++;

			onCkecked();
		}
		else $.ajax(
		{
			'url': 'valid.json',
			'type': 'POST',
			'contentType': 'text/plain',
			'data': code
		})
		.done(function(msg)
		{
			if (msg === true)
			{
				edits[id].getWrapperElement().classList.remove("error");
				edits[id].clearGutter("errors");
				elab.title = "Skrypt jest poprawny";
				good++;
			}
			else if (msg === false)
			{
				edits[id].getWrapperElement().classList.add("error");
				edits[id].clearGutter("errors");
				elab.title = "Skrypt jest niepoprawny";
				bad++;
			}
			else if (typeof msg[0] === "object")
			{
				const marker = document.createElement("div");
				marker.textContent = "✖";
				marker.title = msg[0].str;
				marker.className = "error"

				edits[id].clearGutter("errors");
				edits[id].setGutterMarker(
				    msg[0].line - 1,
				    "errors",
				    marker
				);

				edits[id].getWrapperElement().classList.add("error");
				elab.title = msg[0].str;
				bad++;
			}
			else bad++;
		})
		.fail(function()
		{
			elab.title = "Nie udało się wykonać walidacji"; bad++;
		})
		.always(function()
		{
			onCkecked();
		});
	}

	if (requested == 0) onError('nojob');
}

function onCkecked()
{
	if (good + bad != checks) return;

	if (!bad) onDone('check');
	else onError('check');

	checks = good = bad = 0;
}

function onPaste(str, e)
{
	const el = document.activeElement;

	if (!el || !(el instanceof HTMLTextAreaElement)) return;

	const start = el.selectionStart;
	const end = el.selectionEnd;

	el.value =
		el.value.substring(0, start) +
		str +
		el.value.substring(end);

	const pos = start + str.length;

	el.selectionStart = pos;
	el.selectionEnd = pos;

	e.preventDefault();
}

function onReset()
{
	let sec = document.getElementById('scheds').children;

	if (sh_org == null) onLoad();
	else for (const k in sh_org)
	{
		edits[k].getWrapperElement().classList.remove("error");
		edits[k].clearGutter("errors");
		edits[k].setValue(sh_org[k].code);
		edits[k].refresh();
	}
}

function onUpdate(data)
{
	for (const k in data)
	{
		edits[k].getWrapperElement().classList.remove("error");
		edits[k].clearGutter("errors");
		sh_last[k] = data[k];
	}
}

function onTopicadd(name)
{
	let help = document.getElementById('vars');
	let info = document.createElement('p');

	info.textContent = name;
	help.appendChild(info);
}

function onHelpbatch(dict)
{
	for (const k in dict) onHelpadd(k, dict[k])
}

function onHelpadd(uid, name)
{
	let help = document.getElementById('vars');
	let info = document.createElement('a');

	info.href = `javascript:void(0)`;
	info.title = uid;
	info.textContent = name;
	info.addEventListener("mousedown", e => onPaste(uid, e));
	help.appendChild(info);
}
