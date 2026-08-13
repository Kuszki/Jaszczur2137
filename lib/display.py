from time import time, localtime, sleep_us
from network import WLAN, STA_IF

class HD44780_via_PCF8574:

	PCF_RS = 0x01
	PCF_RW = 0x02
	PCF_EN = 0x04
	PCF_BL = 0x08

	_row_offsets = [None] * 4

	def __init__(self, i2c, i2cAddr = 0x27, rows = 2, cols = 16, en = True):

		self._i2cAddr = i2cAddr
		self._backlight = 0

		self._entrymode = 0x02
		self._displaycontrol = 0x04

		self.i2c = i2c

		self._cols = min(cols, 80)
		self._lines = min(rows, 4)

		functionFlags = 0

		self._row_offsets[0] = 0x00
		self._row_offsets[1] = 0x40
		self._row_offsets[2] = 0x00 + cols
		self._row_offsets[3] = 0x40 + cols

		if rows > 1: functionFlags |= 0x08

		self._write2Wire(0x00, False, False)
		sleep_us(50000)

		self._displaycontrol = 0x04
		self._entrymode = 0x02
		self._backlight = en

		self._sendNibble(0x03)
		sleep_us(4500)
		self._sendNibble(0x03)
		sleep_us(200)
		self._sendNibble(0x03)
		sleep_us(200)
		self._sendNibble(0x02)

		self._send(0x20 | functionFlags)

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

		if isData: i2cData |= self.PCF_RS
		if enable: i2cData |= self.PCF_EN
		if self._backlight: i2cData |= self.PCF_BL

		self.i2c.writeto(self._i2cAddr, i2cData.to_bytes(1, 'big'))

class display:

	INFO = ' %4.1f' + chr(223) + 'C   %4.1f%% '
	DATE = '%02d.%02d.%04d %02d:%02d'

	TMP = '%4.1f' + chr(223) + 'C    %4.1f' + chr(223) + 'C'
	HUM = '%4.1f%%      %4.1f%%'

	def __init__(self, i2c, pin, enc, dth_l, dth_p, tz):

		try: self.disp = HD44780_via_PCF8574(i2c, en = False)
		except: self.disp = None
		else:

			self.pin = pin
			self.enc = enc

			self.dth_l = dth_l
			self.dth_p = dth_p

			self.tz = tz

			self.on = False
			self.last = 0
			self.down = 0
			self.lenc = 0
			self.page = 0

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

	def on_refresh(self, now):

		if self.page == 0:

			temp, rh = self.get_avg()
			t = now + self.tz() * 3600
			t = localtime(t)[0:6]

			self.disp.clear()
			self.disp.moveto(0, 0)
			self.disp.print(self.DATE % (t[2], t[1], t[0], t[3], t[4]))
			self.disp.moveto(1, 0)
			self.disp.print(self.INFO % (temp, rh))

		elif self.page == 1:

			if self.dth_l is not None:
				t_l = self.dth_l.temperature()
				h_l = self.dth_l.humidity()
			else:
				t_l = h_l = 0.0

			if self.dth_l is not None:
				t_r = self.dth_r.temperature()
				h_r = self.dth_r.humidity()
			else:
				t_r = h_r = 0.0

			self.disp.clear()
			self.disp.moveto(0, 0)
			self.disp.print(self.TMP % (t_l, t_r))
			self.disp.moveto(1, 0)
			self.disp.print(self.HUM % (h_l, h_r))

		elif self.page == 2:

			net = WLAN(STA_IF)

			self.disp.clear()
			self.disp.moveto(0, 0)
			self.disp.print(net.config('hostname'))
			self.disp.moveto(1, 0)
			self.disp.print(net.ifconfig()[0])

	def on_loop(self):

		if self.disp is None: return
		else:

			pos = self.enc.value()
			btn = self.pin.value()

			now = time()
			pch = False

		if pos != self.lenc:

			if pos > self.lenc: inc = 1
			else: inc = -1

			self.page = (self.page + inc) % 3
			self.lenc = pos

			btn = False
			pch = True

		if not btn: self.down = now + 15

		if not btn and not self.on:

			self.disp.backlight(True)
			self.on = True

		if self.on and now >= self.down:

			self.disp.backlight(False)
			self.on = False
			self.page = 0

		if pch or now - self.last >= 5:

			self.on_refresh(now)
			self.last = now
