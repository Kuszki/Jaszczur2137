from time import time, localtime, sleep_us

PCF_RS = 0x01
PCF_RW = 0x02
PCF_EN = 0x04
PCF_BACKLIGHT = 0x08

class HD44780_via_PCF8574:

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

		if isData: i2cData |= PCF_RS
		if enable: i2cData |= PCF_EN
		if self._backlight: i2cData |= PCF_BACKLIGHT

		self.i2c.writeto(self._i2cAddr, i2cData.to_bytes(1, 'big'))

class display:

	INFO = '> %4.1f ' + chr(176) +'C   %2.0f' + chr(37) + ' <' # chr(223)
	DATE = '%02d.%02d.%04d %02d:%02d'

	def __init__(self, i2c, pin, temp, rh, tz):

		self.disp = HD44780_via_PCF8574(i2c, en = False)
		self.pin = pin

		self.temp = temp
		self.rh = rh
		self.tz = tz

		self.on = False
		self.last = 0
		self.down = 0

	def on_refresh(self, now):

		t = now + self.tz() * 3600
		t = localtime(t)[0:6]

		self.disp.moveto(0, 0)
		self.disp.print(self.DATE % (t[2], t[1], t[0], t[3], t[4]))
		self.disp.moveto(1, 0)
		self.disp.print(self.INFO % (self.temp(), self.rh()))

	def on_loop(self):

		btn = self.pin.value()
		now = time()

		if not btn: self.down = now + 15

		if not btn and not self.on:

			self.disp.backlight(True)
			self.on = True

		if self.on and now >= self.down:

			self.disp.backlight(False)
			self.on = False

		if now - self.last >= 5:

			self.on_refresh(now)
			self.last = now
