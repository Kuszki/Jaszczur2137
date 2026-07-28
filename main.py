from gc import collect, threshold
from json import dumps, load
from machine import Pin, freq
from dht import DHT22

from output import output
from dthsens import dthsens
from parser import genreport
from driver import driver
from server import server

var = dict()
sens = dict()
outs = dict()

with open("etc/outs.json", "r") as f:
	for k, p in load(f).items():
		outs[k] = output(k, Pin(p, Pin.OUT), var)

dth_l = dthsens(DHT22(Pin(16)), 'tL', 'hL', var)
dth_p = dthsens(DHT22(Pin(17)), 'tP', 'hP', var)

sens.update(dth_l.sensors())
sens.update(dth_p.sensors())

d = driver(outs, sens, var)
s = server()

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

	s.accept()
	d.on_loop()
