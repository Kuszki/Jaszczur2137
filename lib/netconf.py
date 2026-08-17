# coding=UTF-8

from ntptime import settime
from time import sleep

import network, json

def configure():

	with open('/etc/network.json', 'r') as f:
		conf = json.load(f)

	if 'client' in conf:

		net = network.WLAN(network.STA_IF)
		con = conf['client']

		net.active(con.get('on', True))

		if net.active():

			net.config(hostname = con['name'])
			net.config(pm = net.PM_PERFORMANCE)
			net.connect(con['ssid'], con['pass'])

	if 'access' in conf:

		net = network.WLAN(network.AP_IF)
		con = conf['access']

		net.active(con.get('on', True))

		if net.active(): net.config(\
			ssid = con['ssid'], \
			key = con['pass'], \
			hostname = con['name'], \
			security = network.SEC_WPA2, \
			pm = net.PM_PERFORMANCE)

	if 'sync' in conf:

		net = network.WLAN(network.STA_IF)
		con = conf['sync']

		tr = st = con.get("try", 10)
		sl = con.get("sleep", 6)

		while st > 0 and not net.isconnected():

			sleep(sl)
			st -= 1

		if net.isconnected(): synctime(tr, sl)

def synctime(st = 6, sl = 10):

	while st > 0:

		try: settime()
		except:

			sleep(sl)
			st -= 1

		else: st = 0
