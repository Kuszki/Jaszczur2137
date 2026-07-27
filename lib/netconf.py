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

		net.active(bool(int(con['on'])))

		if 'name' in con:
			try: net.config(dhcp_hostname = con['name'])
			except: pass

		if net.active():
			try: net.connect(con['ssid'], con['pass'])
			except: pass

	if 'access' in conf:

		net = network.WLAN(network.AP_IF)
		con = conf['access']

		net.active(bool(int(con['on'])))

		if net.active(): net.config(\
			essid = con['ssid'], password = con['pass'], \
			authmode = network.AUTH_WPA_WPA2_PSK, \
			dhcp_hostname = con['name'])

	if 'sync' in conf:

		synctime(conf['sync']["try"], conf['sync']["sleep"])

def synctime(st = 6, sl = 10):

	while st > 0:

		try: settime()
		except:

			sleep(sl)
			st -= 1

		else: st = 0

def sta_active():

	return network.WLAN(network.STA_IF).active()

def ap_active():

	return network.WLAN(network.AP_IF).active()
