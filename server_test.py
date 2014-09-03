import server

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
