#!/usr/bin/env python

"""
   evaluation script used for the IPM simulations.
"""

# -----------------------------------------------------------------------------------
# (C)opyrights 2008-2011 by Albert Weichselbraun <albert.weichselbraun@wu-wien.ac.at>
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

import sys
import os.path
from csv import writer
from gzip import GzipFile
from eWRT.util.cache import DiskCached
from eWRT.util.async  import Async
from geoTEF.input import CSVResultCollection, SigCSVResultCollection
from geoTEF.dataset.ipm import EqualLR, ILR, ContainsLR, ContainedLR, ContainsOrContainedLR, NeighborLR, ALR, OntologyLR  # ILocationReferences to use for the comparison
from geoTEF.scoring.document import P1DocumentScoring # MaxMatchDocumentScoring
from cPickle import load, UnpicklingError
try:
    import psyco
    psyco.full()
except ImportError:
    pass


TBL_NAME_BINARY = "binary.tex"

USER_PREFERENCES = {
  'tourism': {'ContainsLR' : [ 0., 0., 0.8, 0.95 ],
              'ContainedLR': [ 1., 1., 1., 1. ],
              'NeighborLR' : [ 0., 0., 0.1 ],
              'OntologyLR' : [ 0., 0., 0.   ],
             },
  'media':   {'ContainsLR' : [ 0.5, 0.6, 0.8, 0.9 ],
              'ContainedLR': [ 1., 1., 1., 1. ],
              'NeighborLR' : [ 0., 0.4, 0.8 ],
              'OntologyLR' : [ 0., 0.3, 0.7 ],
             },
}

@DiskCached(".get_corpora-Cache")
def get_corpus(corpusUrl):
    """ retrieves the given corpus using the reader
        specified in the corpusUrl

        @param[in] corpusUrl e.g. CSVResultCollection:/home/..../reuters.csv
        @returns the corpus as dictionary
    """
    assert ":" in corpusUrl
    readerClass, path = corpusUrl.split(":",1)

    reader = eval(readerClass)()
    if path.endswith(".gz"):
        reader.read( GzipFile(path) )
    else:
        reader.read( open(path) )

    return reader


def _get_scoring_method(resultPath, referencePath, ilrString, mode, usecase):
    """ returns the scoring method based on the parameters specified """
    results   = get_corpus( resultPath )
    reference = get_corpus( referencePath )
    ilr       = eval(ilrString)

    for ilrString, preferences in USER_PREFERENCES[usecase].iteritems():
        eval(ilrString).userPrefs = preferences
        
    if mode == 'or':
        scoringMethod = P1DocumentScoring( results, reference, ilr, "|" )
    else:
        scoringMethod = P1DocumentScoring( results, reference, ilr )

    return scoringMethod


@DiskCached("./.ipm-evaluate-worker")
def evaluate(resultPath, referencePath, ilrString, mode, usecase):
    """ evaluates the results based on the reference corpus and the given evaluation logic 
        @param[in] resultPath    ... results from the evaluation method
        @param[in] referencePath ... results from the reference corpus/method
        @param[in] ilrString     ... name of the ILocationReference type to use for the comparison (e..g ContainsLR)
        @return the total score for the given combination 
    """
    scoringMethod = _get_scoring_method(resultPath, referencePath, ilrString, mode, usecase)
    return sum( [ sc for sc in scoringMethod ] )


@DiskCached("./.ipm-evaluate-worker")
def computeDelta(fname, resultPathList, referencePath, ilrString, mode, usecase):
    """ computes the deltas between the usecases and writes them to csv files """
    if os.path.exists( fname ):
        return

    scoringMethodList = [ _get_scoring_method(resultPath, referencePath, ilrString, mode, usecase) for resultPath in resultPathList ]
    wf = open(fname, "w")
    ww = writer( wf  )

    keys = scoringMethodList[0].ref.keys()

    for docId in keys:
        row = [ docId ] + [ sc.next(docId) for sc in scoringMethodList ]
        ww.writerow( row )
        wf.flush()

    wf.close()
    

if len(sys.argv)<2:
    print "Missing arguments...."
    sys.exit(-1)
if sys.argv[1] == "init":
    locations = ['CSVResultCollection:/home/albert/ipm-geoeval/corpora/reuters.csv.gz', 'SigCSVResultCollection:/home/albert/ipm-geoeval/corpora/geoLyzard_Amitay_C100000.csv.gz', 'SigCSVResultCollection:/home/albert/ipm-geoeval/corpora/geoLyzard_Amitay_C5000.csv.gz', 'SigCSVResultCollection:/home/albert/ipm-geoeval/corpora/geoLyzard_Amitay_C500000.csv.gz', 'SigCSVResultCollection:/home/albert/ipm-geoeval/corpora/OpenCalais.csv.gz', 'SigCSVResultCollection:/home/albert/ipm-geoeval/corpora/geoLyzard_Default_C50000.csv.gz', 'SigCSVResultCollection:/home/albert/ipm-geoeval/corpora/geoLyzard_Default_C10000.csv.gz', 'CSVResultCollection:/home/albert/ipm-geoeval/corpora/Alchemy.csv.gz', 'SigCSVResultCollection:/home/albert/ipm-geoeval/corpora/geoLyzard_Amitay_C10000.csv.gz', 'SigCSVResultCollection:/home/albert/ipm-geoeval/corpora/geoLyzard_Default_C500000.csv.gz', 'SigCSVResultCollection:/home/albert/ipm-geoeval/corpora/geoLyzard_Amitay_C50000.csv.gz', 'SigCSVResultCollection:/home/albert/ipm-geoeval/corpora/geoLyzard_Default_C100000.csv.gz', 'SigCSVResultCollection:/home/albert/ipm-geoeval/corpora/geoLyzard_Default_C5000.csv.gz' ]
    for loc in locations:
        print "init",loc, "..."
        get_corpus(loc)
elif sys.argv[1] == "delta":
    fname, resultPathList, referencePath = sys.argv[2], sys.argv[3].split(" "), sys.argv[4]
    computeDelta( fname, resultPathList, referencePath, "OntologyLR", "or", "media" )

elif len(sys.argv)<4:
    print sys.argv, len(sys.argv)
    print "%s [reader:result_corpus] [reader:reference_corpus] [ILR] [and|or]" % sys.argv[0]
    sys.exit(-1)
else:
    print "Starting:", sys.argv
    result_corpus, reference_corpus, ilr, mode, usecase = sys.argv[1:]
    evaluate( result_corpus, reference_corpus, ilr, mode, usecase )
    print "Completed:", sys.argv
    sys.exit(0)  # complete this thread no matter what happens
