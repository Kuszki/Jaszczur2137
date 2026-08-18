# coding=UTF-8

from time import time, localtime, sleep_us
from network import WLAN, STA_IF
from micropython import const
from machine import Pin

_INFO = const(' %04.1f\xDFC   %04.1f%% ')
_DATE = const('%02d.%02d.%04d %02d:%02d')
_TMP = const('%04.1f\xDFC    %04.1f\xDFC')
_HUM = const('%04.1f%%      %04.1f%%')
_FMT = const('%-16s')

_PAGES = const(3)

class HD44780_via_PCF8574:

	_row_offsets = [ 0x00, 0x40 ]

	def __init__(self, i2c, addr = 0x27, en = True):

		self._i2cAddr = addr
		self._backlight = en
		self._displaycontrol = 0

		self.i2c = i2c

		self._write2Wire(0x00, False, False)
		sleep_us(15000)

		self._sendNibble(0x03)
		sleep_us(4200)
		self._sendNibble(0x03)
		sleep_us(110)
		self._sendNibble(0x03)
		sleep_us(110)
		self._sendNibble(0x02)
		sleep_us(40)

		self._send(0x28)
		sleep_us(40)

		self.display()
		self.clear()

	def enable(self):

		self._backlight = True
		self.display(True)

	def disable(self):

		self._backlight = False
		self.display(False)

	def clear(self):

		self._send(0x01)
		sleep_us(1600)

	def home(self):

		self._send(0x02)
		sleep_us(1600)

	def moveto(self, row, col):

		self._send(0x80 | (self._row_offsets[row] + col))

	def display(self, en = True):

		if en: self._displaycontrol |= 0x04
		else: self._displaycontrol &= ~0x04

		self._send(0x08 | self._displaycontrol)

	def backlight(self, en = True):

		self._backlight = en
		self._write2Wire(0x00, True, False)

	def print(self, data):

		for s in str(data): self._send(ord(s), True)

	def _send(self, value, isData = False):

		self._sendNibble((value >> 4 & 0x0F), isData)
		self._sendNibble((value & 0x0F), isData)

	def _sendNibble(self, halfByte, isData = False):

		self._write2Wire(halfByte, isData, True)
		sleep_us(1)
		self._write2Wire(halfByte, isData, False)
		sleep_us(37)

	def _write2Wire(self, halfByte, isData, enable):

		i2cData = halfByte << 4

		if isData: i2cData |= 0x01
		if enable: i2cData |= 0x04
		if self._backlight: i2cData |= 0x08

		self.i2c.writeto(self._i2cAddr, i2cData.to_bytes(1, 'big'))

class display:

	def __init__(self, i2c, pin, enc, dth_l, dth_p, time):

		try: self.disp = HD44780_via_PCF8574(i2c, en = False)
		except: self.disp = None
		else:

			self.pin = pin
			self.enc = enc

			self.dth_l = dth_l
			self.dth_p = dth_p

			self.time = time

			self.irq = False
			self.on = False

			self.last = 0
			self.down = 0
			self.lenc = 0
			self.page = 0

			pin.irq(self._irq, Pin.IRQ_FALLING)

	def _irq(self, pin):

		if pin is self.pin: self.irq = True

	def get_avg(self):

		if self.dth_l is not None and self.dth_p is not None:
			temp = (self.dth_l.temperature() + self.dth_p.temperature()) / 2.0
			rh = (self.dth_l.humidity() + self.dth_p.humidity()) / 2.0
		elif self.dth_l is not None:
			temp = self.dth_l.temperature()
			rh = self.dth_l.humidity()
		elif self.dth_p is not None:
			temp = self.dth_p.temperature()
			rh = self.dth_p.humidity()
		else:
			temp = 0.0
			rh = 0.0

		return temp, rh

	def get_time(self, now = None):

		return localtime(self.time(now))[0:6]

	def on_refresh(self, now = None):

		if self.disp is None: return

		if self.page == 0:

			if now is None: now = time()

			temp, rh = self.get_avg()
			t = self.get_time(now)

			self.disp.moveto(0, 0)
			self.disp.print(_DATE % (t[2], t[1], t[0], t[3], t[4]))
			self.disp.moveto(1, 0)
			self.disp.print(_INFO % (temp, rh))

		elif self.page == 1:

			if self.dth_l is not None:
				t_l = self.dth_l.temperature()
				h_l = self.dth_l.humidity()
			else:
				t_l = h_l = 0.0

			if self.dth_p is not None:
				t_r = self.dth_p.temperature()
				h_r = self.dth_p.humidity()
			else:
				t_r = h_r = 0.0

			self.disp.moveto(0, 0)
			self.disp.print(_TMP % (t_l, t_r))
			self.disp.moveto(1, 0)
			self.disp.print(_HUM % (h_l, h_r))

		elif self.page == 2:

			net = WLAN(STA_IF)

			self.disp.moveto(0, 0)
			self.disp.print(_FMT % net.config('hostname'))
			self.disp.moveto(1, 0)
			self.disp.print(_FMT % net.ifconfig()[0])

	def on_loop(self):

		if self.disp is None: return
		else:

			btn = not self.pin.value()
			pos = self.enc.value()

			now = time()
			inc = 0

		if self.irq:

			self.irq = False
			btn = True

		if pos != self.lenc:

			if pos < self.lenc: inc = -1
			elif pos > self.lenc: inc = 1

			self.page = (self.page + inc) % _PAGES
			self.lenc = pos
			self.last = 0
			btn = True

		if not self.on and btn:

			self.disp.backlight(True)
			self.on = True

		if btn: self.down = now + 15

		if self.on and now >= self.down:

			self.disp.backlight(False)
			self.on = False
			self.page = 0
			self.last = 0

		if now - self.last >= 5:

			self.on_refresh(now)
			self.last = now
