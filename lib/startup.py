from netconf import configure
from machine import freq
from gc import threshold

threshold(32768)
freq(240000000)
configure()
