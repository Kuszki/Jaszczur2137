from gc import collect, threshold
from netconf import configure
from machine import freq

freq(160000000)
threshold(25600)

configure()
collect()
