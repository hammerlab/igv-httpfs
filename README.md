[![Build Status](https://travis-ci.org/hammerlab/igv-httpfs.svg)](https://travis-ci.org/hammerlab/igv-httpfs) [![Coverage Status](https://img.shields.io/coveralls/hammerlab/igv-httpfs.svg)](https://coveralls.io/r/hammerlab/igv-httpfs?branch=coverage)

igv-httpfs
==========

An adaptor which lets IGV talk to HDFS via HttpFS. Blog post [here](http://www.hammerlab.org/2014/12/05/igv-httpfs/).

To run the server:

    (set up virtualenv)
    pip install -r requirements.txt
    ./server.py

To run the tests:

    nosetests
