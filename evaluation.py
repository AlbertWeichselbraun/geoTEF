#!/usr/bin/env python

"""
   evaluation script used for the KDD 2009 simulations.
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

from csv import reader, writer
from geoTEF.dataset.factory import HierarchyLocationReferenceLookup
from geoTEF.dataset.types import HierarchyLocationReference
from geoTEF.scoring.evaluation import ReutersEvaluationDataSetFactory, IdBasedEvaluationDataSetFactory, Evaluation, EvaluationDataSet
from geoTEF.geoTEFconfig import REUTERS_GOLDSTD_REF
from geoTEF.output.gnuplot import GnuPlot
from glob import glob
from sys import stdout


try:
    import psyco
    psyco.full()
except ImportError:
    from warnings import warn
    warn("Cannot import psyco!")

SIMULATION_STEPS=20

def evaluation3d():
    """ create a 3d visualiation of the utility score """
    g = ( GnuPlot(delimiter=","), GnuPlot(delimiter=",") )
    gold = ReutersEvaluationDataSetFactory( REUTERS_GOLDSTD_REF ).get()
    for resultFile in glob("data/results/*.csv"):
        print resultFile," ", 
        tag = IdBasedEvaluationDataSetFactory( resultFile ).get()

        csv_file_out = ( resultFile + "_3d.dat", )
        #png_file_out = ( resultFile + "_super.png", resultFile + "_sub.png" )
        f = [ open(cf, "w") for cf in csv_file_out ]
        cw = [ writer( ff ) for ff in f ]

        for w1 in xrange(0, SIMULATION_STEPS+1):
            if w1% 2 == 0: stdout.write("#"); stdout.flush()
            for w2 in xrange(0, SIMULATION_STEPS+1):
                HierarchyLocationReference.W_SUBCLASS   = w1 /float(SIMULATION_STEPS)
                HierarchyLocationReference.W_SUPERCLASS = w2 /float(SIMULATION_STEPS)
                score = Evaluation.computeScore( EvaluationDataSet( tag, gold ) )
                cw[0].writerow( (w1/float(SIMULATION_STEPS), w2/float(SIMULATION_STEPS), score) )

        print
        [ ff.close() for ff in f ]
        #[ gg.xy_plot(cf, title=resultFile) for gg, cf in zip(g,csv_file_out) ]

    #[ gg.visualize(png) for gg,png in zip(g,png_file_out) ]

def evaluation2d():
    """ create a 2d visualiation of the utility score """
    g = ( GnuPlot(delimiter=","), GnuPlot(delimiter=",") )
    gold = ReutersEvaluationDataSetFactory( REUTERS_GOLDSTD_REF ).get()
    HierarchyLocationReference.W_SUPERCLASS = 0.0

    for resultFile in glob("data/results/*.csv"):
        print resultFile," ", 
        tag = IdBasedEvaluationDataSetFactory( resultFile ).get()

        csv_file_out = ( resultFile + "_2d.dat", )
        #png_file_out = ( resultFile + "_super.png", resultFile + "_sub.png" )
        f = [ open(cf, "w") for cf in csv_file_out ]
        cw = [ writer( ff ) for ff in f ]

        for w1 in xrange(0, SIMULATION_STEPS+1):
            HierarchyLocationReference.W_SUBCLASS   = w1 /float(SIMULATION_STEPS)
            score = Evaluation.computeScore( EvaluationDataSet( tag, gold ) )
            cw[0].writerow( (w1/float(SIMULATION_STEPS), score) )

        print
        [ ff.close() for ff in f ]
        #[ gg.xy_plot(cf, title=resultFile) for gg, cf in zip(g,csv_file_out) ]

    #[ gg.visualize(png) for gg,png in zip(g,png_file_out) ]


evaluation2d()
evaluation3d()

# $Id$

