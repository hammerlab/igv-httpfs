import server

import mock
import requests
import server_test

from nose.tools import *

BROKEN_VCF_DATA = open('testdata/run19.vcf').read()
GOLDEN_VCF_DATA = open('testdata/run19.fixed.vcf').read()

server_test.FAKE_FS['example.vcf/part-r-00000'] = BROKEN_VCF_DATA

@mock.patch('requests.get', server_test.stubbed_get)
def test_stubbed_get():
    url = 'http://localhost:14000/webhdfs/v1/example.vcf/part-r-00000?op=OPEN&user.name=igv'
    eq_(200, requests.get(url).status_code)
    eq_(BROKEN_VCF_DATA, requests.get(url).content)


@mock.patch('requests.get', server_test.stubbed_get)
def test_regular_get():
    start_response = mock.MagicMock()
    response = server.application({
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/example.vcf/part-r-00000',
        'QUERY_STRING': '',
        }, start_response)
    
    expected_response = BROKEN_VCF_DATA
    eq_([expected_response], response)
    start_response.assert_called_once_with('200 OK', [
        ('Content-Type', 'text/plain'),
        ('Content-Length', str(len(expected_response)))])


@mock.patch('requests.get', server_test.stubbed_get)
def test_regular_head():
    start_response = mock.MagicMock()
    response = server.application({
        'REQUEST_METHOD': 'HEAD',
        'PATH_INFO': '/example.vcf/part-r-00000',
        'QUERY_STRING': '',
        }, start_response)
    
    eq_([''], response)
    start_response.assert_called_once_with('200 OK', [
        ('Content-Type', 'text/plain'),
        ('Content-Length', str(len(BROKEN_VCF_DATA)))])


@mock.patch('requests.get', server_test.stubbed_get)
def test_fixed_get():
    start_response = mock.MagicMock()
    response = server.application({
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/example.fixed.vcf',
        'QUERY_STRING': '',
        }, start_response)
    
    expected_response = GOLDEN_VCF_DATA
    eq_([expected_response], response)
    start_response.assert_called_once_with('200 OK', [
        ('Content-Type', 'text/plain'),
        ('Content-Length', str(len(expected_response)))])


@mock.patch('requests.get', server_test.stubbed_get)
def test_fixed_head():
    start_response = mock.MagicMock()
    response = server.application({
        'REQUEST_METHOD': 'HEAD',
        'PATH_INFO': '/example.fixed.vcf',
        'QUERY_STRING': '',
        }, start_response)
    
    expected_response = ''
    eq_([expected_response], response)
    start_response.assert_called_once_with('200 OK', [
        ('Content-Type', 'text/plain'),
        ('Content-Length', str(len(GOLDEN_VCF_DATA)))])
