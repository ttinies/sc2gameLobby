
from __future__ import absolute_import
from __future__ import division       # python 2/3 compatibility
from __future__ import print_function # python 2/3 compatibility

import json
import socket
import time
try:						from urllib2 		import urlopen
except ModuleNotFoundError:	from urllib.request import urlopen

from sc2gameLobby import gameConstants as c

'''
SOURCES:
    http://stackoverflow.com/questions/9481419/how-can-i-get-the-public-ip-using-python2-7
'''


################################################################################
def getAll():
    return (getPublicIPaddress(), getLocalIPaddress(), getMachineIPaddress())


################################################################################
def getMachineIPaddress():
    """visible on this local machine only"""
    return c.LOCALHOST


################################################################################
def getLocalIPaddress():
    """visible to other machines on LAN"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('google.com', 0))
        my_local_ip = s.getsockname()[0] # takes ~0.005s
        #from netifaces import interfaces, ifaddresses, AF_INET
        #full solution in the event of multiple NICs (network interface cards) on the PC
        #def ip4_addresses():
        #    ip_list = []
        #    for interface in interfaces():
        #        for link in ifaddresses(interface)[AF_INET]: # If IPv6 addresses are needed instead, use AF_INET6 instead of AF_INET
        #            ip_list.append(link['addr'])
        #    return ip_list
    except Exception:
        my_local_ip = None
    return my_local_ip # would need to change change if using multiple NICs


################################################################################
def getPublicIPaddress(timeout=c.DEFAULT_TIMEOUT):
    """visible on public internet"""
    start = time.time()
    my_public_ip = None
    e = None
    while my_public_ip == None:
        if time.time() - start > timeout:
            break
        try: #httpbin.org -- site is useful to test scripts / applications.
            my_public_ip = json.load(urlopen('http://httpbin.org/ip'))['origin'] # takes ~0.14s as ipv4
            if my_public_ip: break
        except Exception as e:
            print(type(e), e, "http://httpbin.org/ip")
        try: #jsonip.com -- Seemingly the sole purpose of this domain is to return IP address in JSON.
            my_public_ip = json.load(urlopen('http://jsonip.com'))['ip']  # takes ~0.24s as ipv6
            if my_public_ip: break
        except Exception as e:
            print(type(e), e, "http://jsonip.com")
        try: #ipify.org -- Power of this service results from lack of limits (there is no rate limiting), infrastructure (placed on Heroku, with high availability in mind) and flexibility (works for both IPv4 and IPv6).
            my_public_ip = load(urlopen('https://api.ipify.org/?format=json'))['ip']  # takes ~0.33s
            if my_public_ip: break
        except Exception as e:
            print(type(e), e, "https://api.ipify.org/")
        try: #ip.42.pl -- This is very convenient for scripts, you don't need JSON parsing here.
            my_public_ip = urlopen('http://ip.42.pl/raw').read()  # takes ~0.35s
            if my_public_ip: break
        except Exception as e:
            print(type(e), e, "http://ip.42.pl/raw")
    if not my_public_ip:
        raise e
    return my_public_ip

