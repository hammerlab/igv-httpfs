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


def stubbed_get(path):
    response = 'Every good boy deserves fudge.'
    return response


def test_stubbed_get():
    eq_('Every good boy deserves fudge.', stubbed_get('http://www.google.com/'))


@mock.patch('requests.get', stubbed_get)
def test_stubbing():
    eq_('Every good boy deserves fudge.', requests.get('http://google.com/'))


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
