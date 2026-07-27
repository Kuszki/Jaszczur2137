let set_hiding = null;
let set_locked = false;

let hidden = [];

function onExpand(tree, show = false)
{
	let e = document.getElementById(tree);
	if (e == null) return;

	if (e.className == 'hide')
	{
		e.className = 'off';
		setTimeout(function()
		{
			const i = hidden.indexOf(tree);
			if (i != -1) hidden.splice(i, 1);

			e.className = 'on';
		}, 150);
	}
	else if (!show)
	{
		e.className = 'off';
		setTimeout(function()
		{
			const i = hidden.indexOf(tree);
			if (i == -1) hidden.push(tree);

			e.className = 'hide';
		}, 1000);
	}
}

function onError(code)
{
	let msg = 'Wystąpił błąd';

	if (errors.hasOwnProperty(code))
		msg = errors[code];

	showToast(msg, 5000);
	set_locked = false;
}

function onDone(code)
{
	let msg = 'Wykonano zapytanie';

	if (dones.hasOwnProperty(code))
		msg = dones[code];

	showToast(msg, 5000);
	set_locked = false;
}

function genCell(tr, item)
{
	const td = document.createElement("td");

	function appendItem(parent, item)
	{
		if (item === null) return;

		if (Array.isArray(item))
		{
			for (const sub of item) appendItem(parent, sub);
		}
		else if (typeof item === "object")
		{
			parent.appendChild(item);
		}
		else
		{
			parent.appendChild(document.createTextNode(item));
		}
	}

	appendItem(td, item);
	tr.appendChild(td);
}

function genItem(f, c, t, n, req = false)
{
	let i = document.createElement(c);

	i.type = t;
	i.name = n;
	i.id = n;
	i.required = req;

	f.append(i);

	return i;
}

function genLabel(f, t, p = null, n = null)
{
	let i = document.createElement('label');

	if (p) i.htmlFor = p;
	if (n) i.id = n;

	i.textContent = t;
	f.append(i);

	return i;
}

function genHash(string)
{
	let hash = 0;
	if (string.length == 0) return hash;

	for (let i = 0; i < string.length; i++)
	{
		let charCode = string.charCodeAt(i);

		hash = ((hash << 7) - hash) + charCode;
		hash = hash & hash;
	}

	return hash;
}

function showToast(msg, time)
{
	let x = document.getElementById('toast');

	clearTimeout(set_hiding);
	x.textContent = msg;
	x.className = 'show';

	if (time)
	{
		set_hiding = setTimeout(function()
		{
			x.className = 'hide';

			setTimeout(function()
			{
				x.className = '';
			}, 1000);
		}, time);
	}
}

function hideToast()
{
	let x = document.getElementById('toast');

	clearTimeout(set_hiding);
	x.textContent = msg;
	x.className = 'hide';

	setTimeout(function()
	{
		x.className = '';
	}, 1000);
}
