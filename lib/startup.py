from gc import collect, threshold
from netconf import configure
from machine import freq

freq(240000000)
threshold(32768)

configure()
collect()
