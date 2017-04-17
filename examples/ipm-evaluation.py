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
from sys import stdin,stdout,argv
import gzip
from eWRT.util.async import Async
from geoTEF.input import CSVResultCollection, SigCSVResultCollection
from geoTEF.dataset.ipm import EqualLR, ILR, ContainsLR, ContainedLR, ContainsOrContainedLR, NeighborLR, ALR, OntologyLR  # ILocationReferences to use for the comparison

try:
    import psyco
    psyco.full()
except ImportError:
    pass

IPM_DATA_DIR = path.expanduser("~/evaluation/corpora")
get_corpus = lambda corpus: path.join( IPM_DATA_DIR, corpus )

REFERENCE_URL    = "CSVResultCollection:%s" % get_corpus('reuters.csv.gz')

# maximum number of geo-entities with at least one assigned location according
# to the reuters corpus (= max_score) as computed using compute-max-score.py
MAX_SCORE        = 14917.0 
#MAX_SCORE        = 18854.0

#async = Async("./.ipm-evaluate-worker", max_processes=8, debug_dir="./debug")
async = Async("./.ipm-evaluate-worker", max_processes=24, debug_dir="./debug")


def create_latex_table_results( latex_fname, result, referencePath, method="and", usecase=None ):
    """ creates the output required for the latex table """

    assert usecase
    ilrList = ( "EqualLR", "ContainsLR", "ContainedLR", "ContainsOrContainedLR", "NeighborLR", "OntologyLR", "ALR")
   
    # post jobs
    resultHash = {}
    for geoTaggerName, resultPath in result.items() :
        for ilr in ilrList:
            # print ["./ipm-evaluation-worker.py", resultPath, referencePath, ilr, method, usecase ]
            cmd = ["./ipm-evaluation-worker.py", resultPath, referencePath, ilr, method, usecase ]
            if not path.exists( async.getPostHashfile( cmd ) ):
                print 'Posting', cmd
            resultHash[(resultPath, ilr)] = async.post( cmd )
            
    f=open(latex_fname % usecase, "w")
    print "Fetching results..."
    for geoTaggerName, resultPath in result.items() :
        f.write(" %s & " % geoTaggerName )
        for ilr in ilrList:
            key = resultHash[(resultPath, ilr)]
            print "WAITING for key '%s' (Path:'%s', %s)" % (key, resultPath, ilr)
            stdout.flush()
            res = async.fetch( key )
            f.write("%.1f & " % ( float(res)/MAX_SCORE * 100) )
        f.write("\\\\\n")

    f.close()


def compute_deltas( fname, resultPathList, referencePath ):
    """ creates the output required for the latex table """

    hashList = []
    cmd = [ "./ipm-evaluation-worker.py", "delta", fname, " ".join(resultPathList), referencePath ]
    if not path.exists( async.getPostHashfile( cmd ) ):
         print 'Posting', cmd
    hashList.append( async.post( cmd ) )
    return hashList
 

getUrl     = lambda x: ( ('Alchemy.' in x or 'reuters' in x) and 'CSVResultCollection:' or 'SigCSVResultCollection:')+x
corpusName = lambda x: path.basename(x)[:-7] 
sampleDict = dict( [ (corpusName(fname), getUrl(fname)) for fname in glob(IPM_DATA_DIR+"/*.csv.gz") ]  ) 

if len(argv)<2:
    # binary is the same for all usecases
    create_latex_table_results( "binary-%s.tex", sampleDict, REFERENCE_URL, method="and", usecase='tourism')
    for usecase in ('tourism', 'media'):
        create_latex_table_results( "scalar-%s.tex", sampleDict, REFERENCE_URL, method="or", usecase=usecase )
# compute deltas :)
elif argv[1]=="delta":
    DELTA_SAMPLES = [ 'CSVResultCollection:/home/albert/evaluation/corpora/reuters.csv.gz',
                      'CSVResultCollection:/home/albert/evaluation/corpora/Alchemy.csv.gz',
                      'SigCSVResultCollection:/home/albert/evaluation/corpora/geoLyzard_Default_C500000.csv.gz',
                      'SigCSVResultCollection:/home/albert/evaluation/corpora/geoLyzard_Amitay_C500000.csv.gz',]
    hashList = []
    for reference in DELTA_SAMPLES:
        print "Processing:", reference
        results = [ r for r in DELTA_SAMPLES if r!=reference ] 
        fname = path.basename(reference).split(".")[0]+".csv"
        fpath = path.join("./delta", fname)
        hashList.extend( compute_deltas( fpath, results, reference ) )

    print "Retrieving data..."
    for h in hashList:
        async.fetch( h )


