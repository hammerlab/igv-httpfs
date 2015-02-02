import RangeHTTPServer

from nose.tools import *
from StringIO import StringIO

def test_copy_byte_range():
    inbuffer = StringIO('0123456789abcdefghijklmnopqrstuvwxyz')
    outbuffer = StringIO()

    RangeHTTPServer.copy_byte_range(inbuffer, outbuffer, 4, 10)
    eq_('456789', outbuffer.getvalue())

    outbuffer = StringIO()
    RangeHTTPServer.copy_byte_range(inbuffer, outbuffer, 0, 4)
    eq_('0123', outbuffer.getvalue())

    outbuffer = StringIO()
    RangeHTTPServer.copy_byte_range(inbuffer, outbuffer, 26)
    eq_('qrstuvwxyz', outbuffer.getvalue())
