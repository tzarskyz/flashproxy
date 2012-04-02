#!/usr/bin/env python

import getopt
import httplib
import socket
import re
import sys
import urllib

DEFAULT_REMOTE_ADDR = ""
DEFAULT_REMOTE_PORT = 9000
DEFAULT_FACILITATOR_HOST = "tor-facilitator.bamsoftware.com"
DEFAULT_FACILITATOR_PORT = 9002

class options(object):
    facilitator_addr = None
    remote_addr = None

def usage(f = sys.stdout):
    print >> f, """\
Usage: %(progname)s [HOSTNAME][:PORT]
Register with a flash proxy facilitator using an HTTP POST. By default the
facilitator address is "%(fac_addr)s".

  -a, --address=ADDRESS  register the given address instead of \"%(remote_addr)s\".
  -h, --help             show this help. \
""" % {
    "progname": sys.argv[0],
    "fac_addr": format_addr((DEFAULT_FACILITATOR_HOST, DEFAULT_FACILITATOR_PORT)),
    "remote_addr": format_addr((DEFAULT_REMOTE_ADDR, DEFAULT_REMOTE_PORT)),
}

def parse_addr_spec(spec, defhost = None, defport = None):
    host = None
    port = None
    m = None
    # IPv6 syntax.
    if not m:
        m = re.match(ur'^\[(.+)\]:(\d+)$', spec)
        if m:
            host, port = m.groups()
            af = socket.AF_INET6
    if not m:
        m = re.match(ur'^\[(.+)\]:?$', spec)
        if m:
            host, = m.groups()
            af = socket.AF_INET6
    # IPv4 syntax.
    if not m:
        m = re.match(ur'^(.+):(\d+)$', spec)
        if m:
            host, port = m.groups()
            af = socket.AF_INET
    if not m:
        m = re.match(ur'^:?(\d+)$', spec)
        if m:
            port, = m.groups()
            af = 0
    if not m:
        host = spec
        af = 0
    host = host or defhost
    port = port or defport
    if not port:
        raise ValueError("Bad address specification \"%s\"" % spec)
    return host, int(port)

def format_addr(addr):
    host, port = addr
    if not host:
        return u":%d" % port
    # Numeric IPv6 address?
    try:
        addrs = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM, socket.IPPROTO_TCP, socket.AI_NUMERICHOST)
        af = addrs[0][0]
    except socket.gaierror, e:
        af = 0
    if af == socket.AF_INET6:
        return u"[%s]:%d" % (host, port)
    else:
        return u"%s:%d" % (host, port)

options.facilitator_addr = (DEFAULT_FACILITATOR_HOST, DEFAULT_FACILITATOR_PORT)
options.remote_addr = (DEFAULT_REMOTE_ADDR, DEFAULT_REMOTE_PORT)

opts, args = getopt.gnu_getopt(sys.argv[1:], "a:h", ["address=", "help"])
for o, a in opts:
    if o == "-a" or o == "--address":
        options.remote_addr = parse_addr_spec(a, DEFAULT_REMOTE_ADDR, DEFAULT_REMOTE_PORT)
    elif o == "-h" or o == "--help":
        usage()
        sys.exit()

if len(args) == 0:
    pass
elif len(args) == 1:
    options.facilitator_addr = parse_addr_spec(args[0], DEFAULT_FACILITATOR_HOST, DEFAULT_FACILITATOR_PORT)
else:
    usage(sys.stderr)
    sys.exit(1)

spec = format_addr(options.remote_addr)
http = httplib.HTTPConnection(*options.facilitator_addr)
http.request("POST", "/", urllib.urlencode({"client": spec}))
http.close()

print "Registered \"%s\" with %s." % (spec, format_addr(options.facilitator_addr))