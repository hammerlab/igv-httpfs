import server

import json
import mock
import requests
from testutils import stubbed_get
from types import StringType
import sys

from nose.tools import *


def test_make_httpfs_url():
    eq_('http://localhost:14000/webhdfs/v1/datasets/foo.bam?user.name=igv&op=OPEN',
            server.make_httpfs_url('/datasets/foo.bam'))

    # Tests to write:
    # - setting environment variable httpfs_port
    # - setting environment variable hdfs_user
    # - setting environment variable hdfs_prefix


def test_status_code_response():
    eq_('200 OK', server.status_code_response(200))
    eq_('206 Partial Content', server.status_code_response(206))
    eq_('404 Not Found', server.status_code_response(404))
    eq_('405 Method Not Allowed', server.status_code_response(405))
    eq_('500 Internal Server Error', server.status_code_response(500))


def test_parse_byte_range():
    eq_((0, 499), server.parse_byte_range('bytes=0-499'))
    eq_((987, 1024), server.parse_byte_range('bytes=987-1024'))

@raises(ValueError)
def test_invalid_byte_range():
    server.parse_byte_range('chars=0-1024')


@raises(ValueError)
def test_invalid_byte_range2():
    server.parse_byte_range('bytes=9876-1024')


@mock.patch('requests.get', stubbed_get)
def test_stubbing():
    url = 'http://localhost:14000/webhdfs/v1/b.txt?op=OPEN&user.name=igv'
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
    assert type(response[0]) is StringType  # wsgi requires this.
    start_response.assert_called_once_with('404 Not Found', [
        ('Content-Type', 'text/plain'),
        ('Content-Length', str(len(expected_response)))])


@mock.patch('requests.get', stubbed_get)
def test_wsgi_range_bytes():
    start_response = mock.MagicMock()
    response = server.application({
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/b.txt',
        'QUERY_STRING': '',
        'HTTP_RANGE': 'bytes=5-8'
        }, start_response)

    expected_response = 'is b'
    eq_([expected_response], response)
    start_response.assert_called_once_with('206 Partial Content', [
        ('Content-Type', 'text/plain'),
        ('Content-Length', str(len(expected_response))),
        ('Accept-Ranges', 'bytes'),
        ('Content-Range', 'bytes 5-8/13')])


@mock.patch('requests.get', stubbed_get)
def test_wsgi_head_request():
    start_response = mock.MagicMock()
    response = server.application({
        'REQUEST_METHOD': 'HEAD',
        'PATH_INFO': '/b.txt',
        'QUERY_STRING': '',
        }, start_response)

    expected_response = 'This is b.txt'
    eq_([''], response)  # no response for a HEAD request
    start_response.assert_called_once_with('200 OK', [
        ('Content-Type', 'text/plain'),
        ('Content-Length', str(len(expected_response)))])


@mock.patch('requests.get', stubbed_get)
def test_wsgi_missing_file_head():
    start_response = mock.MagicMock()
    response = server.application({
        'REQUEST_METHOD': 'HEAD',
        'PATH_INFO': '/c.txt',
        'QUERY_STRING': '',
        }, start_response)

    expected_response = 'File /c.txt does not exist.'
    eq_([expected_response], response)
    start_response.assert_called_once_with('404 Not Found', [
        ('Content-Type', 'text/plain'),
        ('Content-Length', str(len(expected_response)))])

@mock.patch('requests.get')
def test_head_only_requests_summary(mock_request):
    '''Pulling an entire 300GB BAM file for a HEAD request would be bad.'''
    httpfs_url = ('http://localhost:14000/webhdfs/v1/b.txt?'
        'user.name=igv&op=getcontentsummary')
    mock_request.return_value = stubbed_get(httpfs_url)
    start_response = mock.MagicMock()
    response = server.application({
        'REQUEST_METHOD': 'HEAD',
        'PATH_INFO': '/b.txt',
        'QUERY_STRING': '',
        }, start_response)

    mock_request.assert_called_once_with(httpfs_url)


@mock.patch('requests.get', stubbed_get)
def test_simple_cors_request():
    start_response = mock.MagicMock()
    response = server.application({
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/b.txt',
        'QUERY_STRING': 'salt=1234',
        'HTTP_ORIGIN': 'example.com'
        }, start_response)

    expected_response = 'This is b.txt'
    eq_([expected_response], response)
    start_response.assert_called_once_with('200 OK', [
        ('Content-Type', 'text/plain'),
        ('Content-Length', str(len(expected_response))),
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Headers', 'Range')])


@mock.patch('requests.get', stubbed_get)
def test_cors_preflight_request():
    start_response = mock.MagicMock()
    response = server.application({
        'REQUEST_METHOD': 'OPTIONS',
        'PATH_INFO': '/b.txt',
        'QUERY_STRING': 'salt=1234',
        'HTTP_ORIGIN': 'example.com',
        'HTTP_ACCESS_CONTROL_REQUEST_HEADERS': 'range',
        'HTTP_ACCESS_CONTROL_REQUEST_METHOD': 'GET'
        }, start_response)

    expected_response = ''
    eq_([expected_response], response)
    start_response.assert_called_once_with('200 OK', [
        ('Access-Control-Allow-Methods', 'HEAD, GET, OPTIONS'),
        ('Access-Control-Max-Age', '1728000'),
        ('Content-Type', 'text/plain'),
        ('Content-Length', '0'),
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Headers', 'Range'),
        ])


def test_update_headers():
    def update_headers(headers, k, v):
        server.update_headers(headers, k, v)
        return headers

    eq_([('k', 'v')], update_headers([], 'k', 'v'))
    eq_([('k', 'v2')], update_headers([('k', 'v')], 'k', 'v2'))
    eq_([('a', 'b'), ('k', 'v')], update_headers([('a', 'b')], 'k', 'v'))
