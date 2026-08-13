from machine import I2C, Pin, Encoder, freq
from gc import collect, threshold
from json import dumps, load
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

try: dth_l = dthsens(DHT22(Pin(25)), 'tL', 'hL', var)
except: dth_l = None
else: sens.update(dth_l.sensors())

try: dth_p = dthsens(DHT22(Pin(26)), 'tP', 'hP', var)
except: dth_p = None
else: sens.update(dth_p.sensors())

enc = Encoder(0, \
	Pin(32, Pin.IN, Pin.PULL_UP), \
	Pin(33, Pin.IN, Pin.PULL_UP), \
	phases = 4, filter_ns = 150)

i2c = I2C(0, scl = Pin(18), sda = Pin(19))
btn = Pin(27, Pin.IN, Pin.PULL_UP)

d = driver(outs, sens, var)
i = display(i2c, btn, enc, dth_l, dth_p, d.get_tzone)

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

	d.on_loop()
	s.accept(75)
	i.on_loop()
