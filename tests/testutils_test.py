from testutils import stubbed_get

from nose.tools import *


def test_stubbed_get():
    url = 'http://localhost:14000/webhdfs/v1/b.txt?op=OPEN&user.name=igv'
    eq_(200, stubbed_get(url).status_code)
    eq_('This is b.txt', stubbed_get(url).content)

    eq_(404, stubbed_get(url.replace('b.txt', 'c.txt')).status_code)
    eq_(404, stubbed_get(url.replace('b.txt', 'c.txt')).status_code)

    partial_url = url + '&offset=5&length=4'
    eq_(200, stubbed_get(partial_url).status_code)
    eq_('is b', stubbed_get(partial_url).content)
