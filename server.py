#!/usr/bin/env python
'''igv-httpfs is a bridge which allows IGV to talk with HttpFS.

It exports a more typical HTTP interface over HttpFS. Differences include:
    - Simpler URLs -- just the path to the file, no parameters allowed
    - Only supports read operations
    - Supports the "Range: bytes" header, which is extensively used by IGV

Usage:
    server.py [port]
    
Respects the following environment variables:
    HTTPFS_ENDPOINT ='http://localhost:14000'
    HDFS_USER       ='igv'
    HDFS_PREFIX     =''
'''

import httplib
import json
import os
import re
import requests
import sys
import urllib
import wsgiref.simple_server

import vcf_fixer


# These are defaults which can be overridden by environment variables.
CONFIG = {
    'HTTPFS_ENDPOINT': 'http://localhost:14000',
    'HDFS_USER': 'igv',
    'HDFS_PREFIX': ''
}
CONFIG.update(os.environ)


def make_httpfs_url(path, user_params={}):
    params = {'user.name': CONFIG['HDFS_USER'], 'op': 'OPEN'}
    params.update(user_params)
    return '%s/webhdfs/v1%s%s?%s' % (
            CONFIG['HTTPFS_ENDPOINT'], CONFIG['HDFS_PREFIX'], path,
            urllib.urlencode(params))


def check_connection():
    url = make_httpfs_url('/', {'op': 'liststatus'})
    response = requests.get(url)
    assert 'FileStatuses' in response, (
        'Unable to connect to HttpFS, request for %s returned %r' % (url, response))


def status_code_response(status_code):
    '''Turns a numeric code into a string, e.g. 404 --> '404 Not Found'.'''
    return str(status_code) + ' ' + httplib.responses[status_code]


def make_response_headers(response_body):
    return [('Content-Type', 'text/plain'),
            ('Content-Length', str(len(response_body)))]


def should_fix(path):
    '''Whether to apply VCF monkey patching.'''
    return '.fixed.' in path


BYTE_RANGE_RE = re.compile(r'bytes=(\d+)-(\d+)')
def parse_byte_range(byte_range):
    '''Returns the two numbers in 'bytes=123-456' or throws ValueError.'''
    m = BYTE_RANGE_RE.match(byte_range)
    if not m:
        raise ValueError('Invalid byte range %s' % byte_range)

    first, last = [int(x) for x in m.groups()]
    if last < first:
        raise ValueError('Invalid byte range %s' % byte_range)
    return first, last


def handle_remote_failure(response):
    status = status_code_response(response.status_code)
    response_body = response.text

    # Attempt to improve the error message
    try:
        exception = response.json()['RemoteException']
        response_body = str(exception['message'])
    except (ValueError, KeyError):
        pass

    return status, make_response_headers(response_body), response_body


def handle_normal_request(path, params={}):
    should_patch = False
    if should_fix(path):
        path = path.replace('.fixed', '') + '/part-r-00000'
        should_patch = True

    url = make_httpfs_url(path, params)
    response = requests.get(url)

    if response.status_code != 200:
        return handle_remote_failure(response)

    status = status_code_response(200)
    response_body = response.content
    if should_patch:
        response_body = vcf_fixer.fix(response_body)
    return status, make_response_headers(response_body), response_body


def handle_head_request(path):
    status, response_headers, response_body = handle_normal_request(
            path, {'op': 'getcontentsummary'})
    if status != '200 OK':
        return status, response_headers, response_body

    length = json.loads(response_body)['ContentSummary']['length']
    response_headers = [('Content-Type', 'text/plain'),
            ('Content-Length', str(length))]
    return status, response_headers, ''


def handle_range_request(environ):
    path = environ['PATH_INFO']
    byte_range_header = environ.get('HTTP_RANGE')
    first, last = parse_byte_range(byte_range_header)
    httpfs_params = {
        'offset': first,
        'length': last - first + 1
    }
    status, response_headers, response_body = handle_normal_request(
            path, httpfs_params)
    if status != '200 OK':
        return status, response_headers, response_body

    # Getting the full length of the file requires a second request.
    # TODO: cache this response.
    stat_url = make_httpfs_url(path, {'op': 'getcontentsummary'})
    try:
        total_length = requests.get(stat_url).json()['ContentSummary']['length']
    except (KeyError, ValueError):
        response_body = 'Unable to get total length of %s' % path
        return (status_code_response(500),
                make_response_headers(response_body), response_body)

    status = status_code_response(206)
    response_headers.extend([
        ('Accept-Ranges', 'bytes'),
        ('Content-Range', 'bytes %s-%s/%s' % (first, last, total_length))
    ])
    return status, response_headers, response_body


def application(environ, start_response):
    '''Required WSGI interface.'''
    request_method = environ['REQUEST_METHOD']

    if request_method not in ['GET', 'HEAD']:
        response_body = 'Method %s not allowed.' % request_method
        start_response(status_code_response(405),
                       make_response_headers(response_body))
        return [response_body]

    byte_range_header = environ.get('HTTP_RANGE')
    if byte_range_header:
        status, response_headers, response_body = handle_range_request(environ)
    else:
        path = environ['PATH_INFO']
        if request_method == 'GET' or should_fix(path):
            status, response_headers, response_body = handle_normal_request(path)
        elif request_method == 'HEAD':
            status, response_headers, response_body = handle_head_request(path)

    start_response(status, response_headers)

    if request_method == 'HEAD' and status == '200 OK':
        response_body = ''
    return [response_body]


def run():
    if len(sys.argv) < 2:
        port = 9876
    else:
        port = int(sys.argv[1])

    #check_connection()
    httpd = wsgiref.simple_server.make_server('0.0.0.0', port, application)
    sys.stderr.write('Listening on 0.0.0.0:%d\n' % port)
    httpd.serve_forever()


if __name__ == '__main__':
    run()
