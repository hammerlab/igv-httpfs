import server

import requests
import mock
from nose.tools import *


def test_make_httpfs_url():
    eq_('http://localhost:14000/webhdfs/v1/datasets/foo.bam?user.name=igv&op=OPEN',
            server.make_httpfs_url('/datasets/foo.bam'))

    # Tests to write:
    # - another op
    # - a byte range
    # - setting FLAGS.httpfs_port
    # - setting FLAGS.hdfs_user
    # - setting FLAGS.hdfs_prefix

FAKE_FS = {
        'a/b/c.txt': 'This is a/b/c.txt',
        'b.txt': 'This is b.txt'
}

def stubbed_get(path):
    prefix = 'http://localhost:14000/webhdfs/v1/'
    if not path.startswith(prefix):
        raise requests.ConnectionError()

    path = path[len(prefix):]
    r = requests.Response()
    if path in FAKE_FS:
        r._content = FAKE_FS[path]
        r.status_code = 200
    else:
        r.status_code = 404
    return r


def test_stubbed_get():
    url = 'http://localhost:14000/webhdfs/v1/b.txt'
    eq_(200, stubbed_get(url).status_code)
    eq_('This is b.txt', stubbed_get(url).content)

    # TODO: non-existent file
    # TODO: invalid host
    # TODO: byte range


@mock.patch('requests.get', stubbed_get)
def test_stubbing():
    url = 'http://localhost:14000/webhdfs/v1/b.txt'
    eq_(200, requests.get(url).status_code)
    eq_('This is b.txt', requests.get(url).content)


@mock.patch('requests.get', stubbed_get)
def test_wsgi_application():
    start_response = mock.MagicMock()
    response = server.application({
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/',
        'QUERY_STRING': '',
        }, start_response)
    
    eq_(['Hello'], response)
    start_response.assert_called_once_with('200 OK', [
        ('Content-Type', 'text/plain'),
        ('Content-Length', str(len('Hello')))])
