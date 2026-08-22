from machine import I2C, Pin
from json import dumps, load
from dht import DHT22

from display import display
from output import output
from dthsens import dthsens
from parser import genreport
from driver import driver
from server import server
from encoder import encoder

var = dict()
sens = dict()
outs = dict()

with open("/etc/outs.json", "r") as f:
	for k, p in load(f).items():
		outs[k] = output(k, Pin(p, Pin.OUT), var)

try: l = dthsens(DHT22(Pin(26)), 'tL', 'hL', var, sens)
except: l = None
else: l.update()

try: p = dthsens(DHT22(Pin(25)), 'tP', 'hP', var, sens)
except: p = None
else: p.update()

e = encoder(Pin(32, Pin.IN), Pin(33, Pin.IN))
d = driver(outs, sens, var)
i = display(I2C(0, scl = Pin(18), sda = Pin(19)), Pin(27, Pin.IN), e, l, p, d.get_time)
s = server(80)

s.defsite('outputs.json', lambda v: dumps(d.get_outputs()))
s.defsite('sensors.json', lambda v: dumps(d.get_sensors()))
s.defsite('variables.json', lambda v: dumps(d.get_variables()))
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
