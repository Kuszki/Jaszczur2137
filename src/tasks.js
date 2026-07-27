const acts = {'0': 'Wyłącz', '1': 'Włącz', '2': 'Auto' };

const errors =
{
	'load': 'Nie udało się wczytać zadań',
	'save': 'Nie udało się zapisać zadań',
	'val': 'Zadane parametry są niepoprawne',
	'id': 'Nie udało się uzyskać identyfikatora',
	'nc': 'Brak zmian do zapisania'
};

const dones =
{
	'save': 'Zadania zostały zapisane'
};

const off = Date.UTC(2000, 0, 1);

let org = null, last = null;
let del = [], add = [];
let outs = [];

function onLoad()
{
	$.ajaxSetup({ 'timeout': 5000 });

	$.when
	(
		$.getJSON('outputs.json'),
		$.getJSON('tasks.json'),
	)
	.done(function(outputs, tasks)
	{
		outs = structuredClone(outputs[0]);

		org = structuredClone(tasks[0]);
		last = structuredClone(tasks[0]);

		onTasks(tasks[0]);
	})
	.fail(function()
	{
		onError('load');
	});
}

function onTasks(data)
{
	let keys = Object.keys(data).sort(function(a, b)
	{
		if (data[a].when < data[b].when) return -1;
		if (data[a].when > data[b].when) return 1;
		return 0;
	});

	for (const k in keys)
	{
		onAppend(keys[k], data[keys[k]]);
	}
}

function onAppend(id, data)
{
	id = Number(id); if (Number.isNaN(id)) return;

	let sec = document.getElementById('tasks');
	let form = document.createElement('form');
	let tab = document.createElement('table');
	let row = document.createElement('tr');

	let cols = []; for (i = 0; i < 6; ++i)
	{
		col = document.createElement('td');
		row.appendChild(col);
		cols.push(col);
	}

	let sid = '[' + id + ']';

	let dat = data['when'] * 1000 + off;
	let lab = genLabel(form, '•', null, 'tlab' + sid);
	let suid = genItem(form, 'select', null, 'uid' + sid, true);
	let dwhen = genItem(form, 'input', 'datetime-local', 'dwhen' + sid, true);
	let sact = genItem(form, 'select', null, 'job' + sid, true);
	let bdel = genItem(form, 'input', 'button', 'tdel' + sid);

	for (k in outs)
	{
		let opt = document.createElement('option');
		opt.textContent = outs[k]['name'];
		opt.value = outs[k]['uid'];
		suid.appendChild(opt);
	}

	for (k in acts)
	{
		let opt = document.createElement('option');
		opt.textContent = acts[k];
		opt.value = k;
		sact.appendChild(opt);
	}

	bdel.onclick = function()
	{
		onRemove(id);
	}

	dwhen.valueAsNumber = dat;
	dwhen.min = new Date();
	sact.value = data['job'];
	bdel.value = 'Usuń';

	cols[0].appendChild(lab);
	cols[1].appendChild(suid);
	cols[2].appendChild(dwhen);
	cols[3].textContent = ':';
	cols[4].appendChild(sact);
	cols[5].appendChild(bdel);

	tab.appendChild(row);
	form.appendChild(tab);
	sec.appendChild(form);

	form.id = 'task_' + id;
}

function onAdd()
{
	if (set_locked) return;
	else set_locked = true;

	$.get('genid.var?task')
	.done(function(data)
	{
		add.push(Number(data));
		onExpand('tasks', true);
		onAppend(data, {});
		set_locked = false;
	})
	.fail(function()
	{
		onError('id');
	});
}

function onRemove(id)
{
	document.getElementById('task_' + id).remove();

	let n = add.indexOf(id);

	if (n > -1) add.splice(n, 1);
	else del.push(id);
}

function onSave()
{
	if (set_locked) return;
	else set_locked = true;

	let sec = document.getElementById('tasks').children;
	let req = {}, ch = false, ok = true;

	for (k in del) { req[del[k]] = { 'del': true }; ch = true; }
	for (i = 0; i < sec.length; ++i)
	{
		let id = Number(sec[i].id.replace('task_', ''));

		let sid = '[' + id + ']';
		let org = last[id];

		let euid = document.getElementById('uid' + sid);
		let ejob = document.getElementById('job' + sid);
		let edate = document.getElementById('dwhen' + sid);

		let job = Number(ejob.value);
		let uid = String(euid.value);

		let when = Number((edate.valueAsNumber - off) / 1000);

		ok = ok &&
			ejob.validity.valid &&
			edate.validity.valid;

		const sc =
		{
			'when': when,
			'job': job,
			'uid': uid
		};

		const is_ch = org == null ||
			sc.when != org.when ||
			sc.job != org.job;

		if (is_ch)
		{
			req[id] = sc;
			ch = true;
		}
	}

	if (ch && ok) showToast('Zapisywanie zmian...', 0);

	if (!ch) onError('nc');
	else if (!ok) onError('val');
	else	$.ajax(
	{
		'url': 'taskup',
		'type': 'POST',
		'contentType': 'application/json',
		'data': JSON.stringify(req)
	})
	.done(function(msg)
	{
		if (msg == "True")
		{
			onUpdate(req);
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

function onReset()
{
	let sec = document.getElementById('tasks').children;

	while (sec.length) sec[0].remove();

	if (org == null) onLoad();
	else onTasks(org);

	onExpand('tasks', true);
}

function onUpdate(data)
{
	for (const k in data)
		last[k] = data[k];
}
