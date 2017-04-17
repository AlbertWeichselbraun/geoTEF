#!/usr/bin/env python

"""
   evaluation script used for the IPM simulations.
"""

# -----------------------------------------------------------------------------------
# (C)opyrights 2008-2010 by Albert Weichselbraun <albert.weichselbraun@wu-wien.ac.at>
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

from os import path, makedirs
from commands import getoutput
from glob import glob
import gzip
from eWRT.util.async import Async
from geoTEF.output import Diagram
from geoTEF.output.writer import EchoCSVWriter
from geoTEF.output.gnuplot import GnuPlot
from geoTEF.input import CSVResultCollection, SigCSVResultCollection
from geoTEF.dataset.ipm import EqualLR, ILR, ContainsLR, ContainedLR, ContainsOrContainedLR, NeighborLR, ALR, OntologyLR  # ILocationReferences to use for the comparison
from shutil import rmtree

try:
    import psyco
    psyco.full()
except ImportError:
    pass

PLOT_DIR     = "./plots"
IPM_DATA_DIR = path.expanduser("~/evaluation/corpora")
get_corpus = lambda corpus: path.join( IPM_DATA_DIR, corpus )

REFERENCE_URL    = "CSVResultCollection:%s" % get_corpus('reuters.csv.gz')
GAZETTEER_LIST   = ('C5000', 'C10000', 'C50000', 'C100000', 'C500000')

# maximum number of geo-entities with at least one assigned location according
# to the reuters corpus (= max_score) as computed using compute-max-score.py
MAX_SCORE        = 14917.0 
#MAX_SCORE        = 18854.0

trans = lambda x: float(x)/MAX_SCORE*100
async = Async("./.ipm-evaluate-worker", max_processes=16)

def _create_plot_dir( dirName ):
    if path.exists( dirName ):
        rmtree( dirName )
    makedirs( dirName )


def add_reference_plot( g, name, ilr, method, usercase ):
    """ adds a reference plot to the given one """
    # determine the correct corpus handle
    for corpusName, corpusUrl in sampleDict.iteritems():
        if name in corpusName:
            resultPath = corpusUrl
            break

    cmd = ["./ipm-evaluation-worker.py", resultPath, REFERENCE_URL, ilr, method, usecase ]
    key = async.getPostHashfile( cmd )
    res = async.fetch( key )

    g.suggest_max_range('y', trans(res))

    d = Diagram()
    for gazetteerNumber, gazetteerName in enumerate( GAZETTEER_LIST ):
        d.add_data_point( (gazetteerNumber, trans(res)) )

    fname = path.join( PLOT_DIR, 'plot-%s_%s-%s-%s.csv' % (name, ilr, method, usecase) )
    f = open( fname, 'w' )
    f.write( d.output( EchoCSVWriter() ) )
    f.close()

    g.xy_plot( fname, title='%s (%s)' % (name, ilr) )


def create_plots( plot_fname, result, referencePath, usecase ):
    """ create the comparison plots """

    method = "or"
    ilrList = ( "EqualLR", "ContainsLR", "ContainedLR", "ContainsOrContainedLR", "NeighborLR", "ALR", "OntologyLR" )
   
    # post jobs
    resultHash = {}
    for geoTaggerName, resultPath in result.items() :
        for ilr in ilrList:
            # print ["./ipm-evaluation-worker.py", resultPath, referencePath, ilr, method, usecase ]
            resultHash[(resultPath, ilr)] = async.getPostHashfile( ["./ipm-evaluation-worker.py", resultPath, referencePath, ilr, method, usecase ] )

    for ilr in ilrList:
        print "ILR", ilr
        geoTagger = geoTaggerName.split("_")[0]
        getCorpusUrl = lambda alg, gaz, dis: "SigCSVResultCollection:" + get_corpus( "geoLyzard_%s_%s%s.csv.gz" % (alg, gaz, dis)) 
        for algorithm in ('Amitay', 'Default'):
            g = GnuPlot(delimiter='\\t')
            g.suggest_min_range('y', 0)
            g.suggest_min_range('y', 100)
            g.set_option( "xtics", "(%s)" % ", ".join( ["'%s' %s" % (gaz, val) for val, gaz in enumerate( GAZETTEER_LIST )])  )
            pname = path.join( PLOT_DIR, 'plot-%s-%s-%s-%s.png' % (algorithm, ilr, method, usecase))

            add_reference_plot( g, 'OpenCalais', ilr, method, usecase )
            add_reference_plot( g, 'reuters', ilr, method, usecase )
            add_reference_plot( g, 'Alchemy', ilr, method, usecase )

            for disambParameters, disambDesc in ( ('', 'medium'), ('_largeEntities', 'large'), ( '_smallerEntities', 'small') ):
                d = Diagram()
                for gazetteerNumber, gazetteerName in enumerate( GAZETTEER_LIST ):
                    resultPath = getCorpusUrl(algorithm, gazetteerName, disambParameters)
                    key = resultHash[(resultPath, ilr)]
                    res = async.fetch( key )
                    d.add_data_point( (gazetteerNumber, trans(res)) )
                    g.suggest_max_range('y', trans(res) )

                fname = path.join( PLOT_DIR, 'plot-%s-%s%s-%s-%s.csv' % (algorithm, ilr, disambParameters, method, usecase)) 
                f = open( fname, 'w' )
                f.write( d.output( EchoCSVWriter() ) )
                f.close()

                g.xy_plot( fname, title='%s (%s; %s)' %(algorithm, ilr, disambDesc))

            # save the graph :)
            g.visualize( pname )

def create_potential_plots( plot_fname, result, referencePath):
    """ create the comparison plots """

    ilrList = ( "EqualLR", "ContainsLR", "ContainedLR", "ContainsOrContainedLR", "NeighborLR", "ALR", "OntologyLR" )
   
    for ilr in ilrList:
        print "ILR", ilr
        for algorithm in ('Amitay', 'Default'):
            g = GnuPlot(delimiter='\\t')
            g.set_option( "xtics", "(%s)" % ", ".join( ["'%s' %s" % (gaz, val) for val, gaz in enumerate( GAZETTEER_LIST )])  )

            g.suggest_min_range('y', 0)
            g.suggest_max_range('y', 100)
            pname = path.join( PLOT_DIR, 'potential-%s-%s.png' % (algorithm, ilr))

            for method, usecase, methodLabel in ( ('and', 'tourism', 'potential'), ('or', 'tourism', 'tourism use case'), ('or', 'media', 'media use case')):
                _add_diagram( g, algorithm, methodLabel, referencePath, ilr, method, usecase )
            # save the graph :)
            g.visualize( pname )


def _add_diagram(g, algorithm, methodLabel, referencePath, ilr, method, usecase, dis='' ):
    getCorpusUrl = lambda alg, gaz, dis: "SigCSVResultCollection:" + get_corpus( "geoLyzard_%s_%s%s.csv.gz" % (alg, gaz, dis)) 
    d = Diagram()
    for gazetteerNumber, gazetteerName in enumerate( GAZETTEER_LIST ):
        resultPath = getCorpusUrl(algorithm, gazetteerName, dis)
        key = async.getPostHashfile( ["./ipm-evaluation-worker.py", resultPath, referencePath, ilr, method, usecase ] )
        res = async.fetch( key )
        d.add_data_point( (gazetteerNumber, trans(res)) )
        g.suggest_max_range('y', trans(res) )

    fname = path.join( PLOT_DIR, 'plot-%s-%s-%s-%s.csv' % (algorithm, ilr, method, usecase)) 
    f = open( fname, 'w' )
    f.write( d.output( EchoCSVWriter() ) )
    f.close()

    g.xy_plot( fname, title='%s (%s; %s)' %(algorithm, ilr, methodLabel))


def create_custom_plots( result, referencePath):
    """ create the comparison plots """

    for dis in ('', '_largeEntities', '_smallerEntities'):
        for algorithm in ('Amitay', 'Default'):
            g = GnuPlot(delimiter='\\t')
            g.set_option( "xtics", "(%s)" % ", ".join( ["'%s' %s" % (gaz, val) for val, gaz in enumerate( GAZETTEER_LIST )])  )

            g.suggest_min_range('y', 0)
            g.suggest_max_range('y', 100)
            pname = path.join( PLOT_DIR, 'compare-suggested-alg-%s-%s.png' % (algorithm, dis))

            for ilr, method, usecase, methodLabel in ( ('OntologyLR', 'or', 'tourism', 'tourism use case'), 
                                                       ('OntologyLR', 'or', 'media', 'media use case'),
                                                       ('EqualLR', 'or', 'media', '=')):
                _add_diagram( g, algorithm, methodLabel, referencePath, ilr, method, usecase, dis=dis )
            # save the graph :)
            g.visualize( pname )


getUrl     = lambda x: ( ('Alchemy.' in x or 'reuters' in x) and 'CSVResultCollection:' or 'SigCSVResultCollection:')+x
corpusName = lambda x: path.basename(x)[:-7] 
sampleDict = dict( [ (corpusName(fname), getUrl(fname)) for fname in glob(IPM_DATA_DIR+"/*.csv.gz") ]  ) 


_create_plot_dir( PLOT_DIR )
# potential plot
create_potential_plots( "potential-%s.png", sampleDict, REFERENCE_URL)
create_custom_plots(sampleDict, REFERENCE_URL)

for usecase in ('tourism', 'media'):
    create_plots( "scalar-%s.png", sampleDict, REFERENCE_URL, usecase=usecase )

getoutput("tar cvjf ./plots.tar.bz2 %s" % PLOT_DIR ) 

