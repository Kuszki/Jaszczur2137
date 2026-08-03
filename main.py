from gc import collect, threshold
from json import dumps, load
from machine import I2C, Pin, freq
from dht import DHT22

from display import display
from output import output
from dthsens import dthsens
from parser import genreport
from driver import driver
from server import server

s = server()
var = dict()
sens = dict()
outs = dict()

with open("/etc/outs.json", "r") as f:
	for k, p in load(f).items():
		outs[k] = output(k, Pin(p, Pin.OUT), var)

try: dth_l = dthsens(DHT22(Pin(27)), 'tL', 'hL', var)
except: dth_l = None
else: sens.update(dth_l.sensors())

try: dth_p = dthsens(DHT22(Pin(32)), 'tP', 'hP', var)
except: dth_p = None
else: sens.update(dth_p.sensors())

if dth_l is not None and dth_p is not None:
	temp = lambda: (dth_l.temperature() + dth_p.temperature()) / 2
	rh = lambda: (dth_l.humidity() + dth_p.humidity()) / 2
elif dth_l is not None:
	temp = dth_l.temperature
	rh = dth_l.humidity
elif dth_p is not None:
	temp = dth_p.temperature
	rh = dth_p.humidity
else:
	temp = lambda: 0.0
	rh = lambda: 0.0

d = driver(outs, sens, var)
i = display(I2C(0), Pin(33, Pin.IN, Pin.PULL_UP), temp, rh, d.get_tzone)

s.defsite('outputs.json', lambda v: dumps(d.get_outputs()))
s.defsite('sensors.json', lambda v: dumps(d.get_sensors()))
s.defsite('units.json', lambda v: dumps(d.get_units()))
s.defsite('prefs.json', lambda v: dumps(d.get_params()))
s.defsite('tasks.json', lambda v: dumps(d.get_tasks()))
s.defsite('history.json', lambda v: dumps(d.get_hist()))
s.defsite('devinfo.json', lambda v: dumps(d.get_devinfo()))
s.defsite('timing.json', lambda v: dumps(d.get_timing()))
s.defsite('valid.json', lambda v: dumps(genreport(v, var)))

s.defsite('genid.var', lambda v: d.get_uids(v))

s.defsite('config', lambda v: d.set_params(v))
s.defsite('taskup', lambda v: d.set_tasks(v))
s.defsite('codeup', lambda v: d.set_scripts(v))
s.defsite('power', lambda v: d.set_power(v))
s.defsite('driver', lambda v: d.set_driver(v))

threshold(25600)
freq(240000000)
collect()

while True:

	s.accept(75)
	d.on_loop()
	i.on_loop()

