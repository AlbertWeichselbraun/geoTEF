#!/usr/bin/env python

"""
   evaluation script used for the IPM simulations.
"""

# -----------------------------------------------------------------------------------
# (C)opyrights 2008-2009 by Albert Weichselbraun <albert.weichselbraun@wu-wien.ac.at>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# -----------------------------------------------------------------------------------

__author__   = "Albert Weichselbraun"
__revision__ = "$Id$"

from os import path
from glob import glob
from sys import stdin,stdout
import gzip
from eWRT.util.async import Async
from geoTEF.input import CSVResultCollection, SigCSVResultCollection
from geoTEF.dataset.ipm import EqualLR, ILR, ContainsLR, ContainedLR, ContainsOrContainedLR, NeighborLR, ALR, OntologyLR  # ILocationReferences to use for the comparison

try:
    import psyco
    psyco.full()
except ImportError:
    pass

IPM_DATA_DIR = path.expanduser("~/ipm-geoeval/corpora")
get_corpus = lambda corpus: path.join( IPM_DATA_DIR, corpus )

REFERENCE_URL    = "CSVResultCollection:%s" % get_corpus('reuters.csv.gz')

#async = Async("./.ipm-evaluate-worker", max_processes=8, debug_dir="./debug")
async = Async("./.ipm-evaluate-worker", max_processes=8, debug_dir="./debug")

def list_hashes( result, referencePath, method, usecase ):
    """ creates the output required for the latex table """

    # ilrList = ( "EqualLR", "ContainsLR", "ContainedLR", "ContainsOrContainedLR", "NeighborLR", "ALR", "OntologyLR" )
    ilrList = ( "NeighborLR", )
  
    # post jobs
    resultHash = {}
    for geoTaggerName, resultPath in result.items() :
        for ilr in ilrList:
            # print ["./ipm-evaluation-worker.py", resultPath, referencePath, ilr, method, usecase ]
            cmd = ["./ipm-evaluation-worker.py", resultPath, referencePath, ilr, method, usecase ]
            if path.exists( async.getPostHashfile( cmd ) ):
                print async.getPostHashfile( cmd )

getUrl     = lambda x: ( ('Alchemy.' in x or 'reuters' in x) and 'CSVResultCollection:' or 'SigCSVResultCollection:')+x
corpusName = lambda x: path.basename(x)[:-7] 
sampleDict = dict( [ (corpusName(fname), getUrl(fname)) for fname in glob(IPM_DATA_DIR+"/*.csv.gz") ]  ) 
#print sampleDict.values()
#print REFERENCE_URL
#sys.exit(0)

# binary is the same for all usecases
for usecase in ('tourism', 'media'):
    list_hashes( sampleDict, REFERENCE_URL, method="or", usecase=usecase )
    list_hashes( sampleDict, REFERENCE_URL, method="and", usecase=usecase )

