[![Build Status](https://travis-ci.org/hammerlab/igv-httpfs.svg)](https://travis-ci.org/hammerlab/igv-httpfs)

igv-httpfs
==========

An adaptor which lets IGV talk to HDFS via HttpFS

To run the server:

    (set up virtualenv)
    pip install -r requirements.txt
    ./server.py

To run the tests:

    nosetests
