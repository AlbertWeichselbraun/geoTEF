#!/bin/sh
# adjust pythonpath to run geoTEF
#
# You need the easy Web Retrieval Toolkit to run this application,
# which is available at
#   http://www.semanticlab.net/index.php/eWRT

EWRT=`pwd`/..                      # directory with your eWRT installation; adjust this
                                   # to your needs
  
export PYTHONPATH=$EWRT:`pwd`

