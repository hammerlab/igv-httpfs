import server

import mock
from nose.tools import *
from testutils import stubbed_get
import requests
import zlib


STD_REQUEST = {
    'REQUEST_METHOD': 'GET',
    'PATH_INFO': '/b.txt',
    'QUERY_STRING': '',
    'HTTP_ACCEPT_ENCODING': 'gzip'
}

def update(obj, k, v):
    '''Returns a new object with a modified or added key/value.'''
    o = obj.copy()
    o[k] = v
    return o


@mock.patch('requests.get', stubbed_get)
@mock.patch('zlib.compress')
def test_simple_gzip(mock_compress):
    mock_compress.return_value = 'shrunk!'
    start_response = mock.MagicMock()
    response = server.application(STD_REQUEST, start_response)

    mock_compress.assert_called_once_with('This is b.txt', 6)
    expected_response = 'shrunk!'
    eq_([expected_response], response)
    start_response.assert_called_once_with('200 OK', [
        ('Content-Type', 'text/plain'),
        ('Content-Length', str(len(expected_response))),
        ('Content-Encoding', 'gzip')])


@mock.patch('requests.get', stubbed_get)
@mock.patch('zlib.compress')
def test_compression_backfires(mock_compress):
    mock_compress.return_value = 'something really long!'
    start_response = mock.MagicMock()
    response = server.application(STD_REQUEST, start_response)

    expected_response = 'This is b.txt'
    eq_([expected_response], response)
    start_response.assert_called_once_with('200 OK', [
        ('Content-Type', 'text/plain'),
        ('Content-Length', str(len(expected_response)))])


@mock.patch('requests.get', stubbed_get)
@mock.patch('zlib.compress')
def test_head_does_not_compress(mock_compress):
    mock_compress.return_value = 'shrunk!'
    start_response = mock.MagicMock()
    response = server.application(
        update(STD_REQUEST, 'REQUEST_METHOD', 'HEAD'),
        start_response)

    eq_(False, mock_compress.called)  # should never be called
    expected_response = 'This is b.txt'
    eq_([''], response)
    start_response.assert_called_once_with('200 OK', [
        ('Content-Type', 'text/plain'),
        ('Content-Length', str(len(expected_response)))])


@mock.patch('requests.get', stubbed_get)
@mock.patch('zlib.compress')
def test_gzipped_range_request(mock_compress):
    # this should compress just the range that was requested.
    mock_compress.return_value = 's!'
    start_response = mock.MagicMock()
    response = server.application(
        update(STD_REQUEST, 'HTTP_RANGE', 'bytes=5-8'),
        start_response)

    mock_compress.assert_called_once_with('is b', 6)
    expected_response = 's!'
    eq_([expected_response], response)
    start_response.assert_called_once_with('206 Partial Content', [
        ('Content-Type', 'text/plain'),
        ('Content-Length', str(len(expected_response))),
        ('Accept-Ranges', 'bytes'),
        ('Content-Range', 'bytes 5-8/13'),
        ('Content-Encoding', 'gzip')])
