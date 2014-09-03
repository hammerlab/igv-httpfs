#!/usr/bin/env python
'''igv-httpfs is a bridge which allows IGV to talk with HttpFS.

It exports a more typical HTTP interface over HttpFS. Differences include:
    - Simpler URLs -- just the path to the file, no parameters allowed
    - Only supports read operations
    - Supports the "Range: bytes" header, which is extensively used by IGV

Usage:
    server.py [--httpfs_port 14000] [--hdfs_user igv] [--hdfs_prefix /path/to/root] [port]
'''

import urllib

import requests
import gflags
FLAGS = gflags.FLAGS


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


def run():
    check_connection()


if __name__ == '__main__':
    run()
