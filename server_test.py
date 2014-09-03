import server

import json
import mock
import requests
import urlparse

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

def stubbed_get(url):
    prefix = 'http://localhost:14000/webhdfs/v1/'
    if not url.startswith(prefix):
        raise requests.ConnectionError()

    parsed_url = urlparse.urlparse(url)
    assert parsed_url.path.startswith('/webhdfs/v1/')
    path = parsed_url.path[len('/webhdfs/v1/'):]

    r = requests.Response()
    if path in FAKE_FS:
        r._content = FAKE_FS[path]
        r.status_code = 200
    else:
        r.status_code = 404
        r._content = json.dumps({
            'RemoteException': {
                'message': 'File /%s does not exist.' % path,
                'exception': 'FileNotFoundException'
            }
        })
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
        'PATH_INFO': '/b.txt',
        'QUERY_STRING': '',
        }, start_response)
    
    expected_response = 'This is b.txt'
    eq_([expected_response], response)
    start_response.assert_called_once_with('200 OK', [
        ('Content-Type', 'text/plain'),
        ('Content-Length', str(len(expected_response)))])


@mock.patch('requests.get', stubbed_get)
def test_wsgi_missing_file():
    start_response = mock.MagicMock()
    response = server.application({
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/c.txt',
        'QUERY_STRING': '',
        }, start_response)
    
    expected_response = 'File /c.txt does not exist.'
    eq_([expected_response], response)
    start_response.assert_called_once_with('404 Not Found', [
        ('Content-Type', 'text/plain'),
        ('Content-Length', str(len(expected_response)))])
