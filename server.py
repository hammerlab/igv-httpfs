#!/usr/bin/env python
'''igv-httpfs is a bridge which allows IGV to talk with HttpFS.

It exports a more typical HTTP interface over HttpFS. Differences include:
    - Simpler URLs -- just the path to the file, no parameters allowed
    - Only supports read operations
    - Supports the "Range: bytes" header, which is extensively used by IGV

Usage:
    server.py [--httpfs_port 14000] [--hdfs_user igv] [--hdfs_prefix /path/to/root] [port]
'''

import httplib
import json
import sys
import urllib
import wsgiref.simple_server


import gflags
FLAGS = gflags.FLAGS
import requests


gflags.DEFINE_integer(
        'httpfs_port', 14000,
        'Port on which HttpFS is running.')

gflags.DEFINE_string(
        'hdfs_user', 'igv',
        'User to pass to HttpFS for pseudo-authentication.')

gflags.DEFINE_string(
        'hdfs_prefix', '',
        'Set to restrict requests to a particular HDFS directory. If you set '
        'this to "/a/b/c", then a request for "d/e.txt" will look for '
        'a/b/c/d/e.txt on HDFS.')


def make_httpfs_url(path, user_params={}):
    params = {'user.name': FLAGS.hdfs_user, 'op': 'OPEN'}
    params.update(user_params)
    return 'http://localhost:%s/webhdfs/v1%s%s?%s' % (
            FLAGS.httpfs_port, FLAGS.hdfs_prefix, path,
            urllib.urlencode(params))


def check_connection():
    url = make_httpfs_url('/', {'op': 'liststatus'})
    response = requests.get(url)
    assert 'FileStatuses' in response, (
        'Unable to connect to HttpFS, request for %s returned %r' % (url, response))


def status_code_response(status_code):
    '''Turns a numeric code into a string, e.g. 404 --> '404 Not Found'.'''
    return str(status_code) + ' ' + httplib.responses[status_code]


def handle_remote_failure(response, start_response):
    status = status_code_response(response.status_code)
    response_body = response.text

    # Attempt to improve the error message
    try:
        exception = response.json()['RemoteException']
        response_body = exception['message']
    except ValueError, KeyError:
        pass

    response_headers = [('Content-Type', 'text/plain'),
                        ('Content-Length', str(len(response_body)))]
    start_response(status, response_headers)
    return [response_body]


def application(environ, start_response):
    '''Required WSGI interface.'''
    request_method = environ['REQUEST_METHOD']
    path = environ['PATH_INFO']
    query = environ['QUERY_STRING']
    byte_range = environ.get('HTTP_RANGE')

    url = make_httpfs_url(path)
    response = requests.get(url)

    if response.status_code != 200:
        return handle_remote_failure(response, start_response)

    status = status_code_response(200)
    response_body = response.content
    response_headers = [('Content-Type', 'text/plain'),
                        ('Content-Length', str(len(response_body)))]
    start_response(status, response_headers)

    # Return the response body.
    # Notice it is wrapped in a list although it could be any iterable.
    return [response_body]


def run():
    try:
        argv = FLAGS(sys.argv)
    except gflags.FlagsError, e:
        sys.stderr.write('%s\n' % e)
        sys.exit(1)

    if len(argv) < 2:
        port = 9876
    else:
        port = int(argv[1])

    #check_connection()
    httpd = wsgiref.simple_server.make_server('localhost', port, application)
    sys.stderr.write('Listening on localhost:%d\n' % port)
    httpd.serve_forever()


if __name__ == '__main__':
    run()
