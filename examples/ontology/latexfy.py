#!/usr/bin/env python
"""
  transforms the output of the ontology-evaluator to /LaTeX/ tables 
"""
# -----------------------------------------------------------------------------------
# latexfy
# geoTEF - geo Tagger Evaluation Framework
# (C)opyrights 2010 by Albert Weichselbraun <albert.weichselbraun@wu.ac.at>
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
__revision__ = "$Revision: 389 $"

from csv import reader, writer
from re import compile as re_compile, I as re_I
from os import path
from numpy import array
from scipy.stats import pearsonr
from glob import glob
from operator import itemgetter

DST_DIRECTORY = "/home/albert/data/ac/research/inwork/pakdd2011-ontology-evaluation/tables"
CORRELATION_REF_FILE = path.join( DST_DIRECTORY, "final_assessment.csv")

WEEK = "week8"
FILES = ( (path.join('results/', WEEK, 'terminology.csv'), 'terminology.tex',),
          (path.join('results/', WEEK, 'relation-types.csv'), 'relation-types.tex'), 
          (path.join('results/', WEEK, 'coherence.csv'), 'coherence.tex'), 
          ('final-assessment.csv', 'final-assessment.tex')
        )

# FILES = [ (f, path.splitext(f)[0]+".tex") for f in glob("*.csv") ]
RE_NAME = re_compile("risk_(\w+)")

# maximum size of concepts; 
# above this size we consider concepts as descriptions and do not include the map in the evaluation
NO_PHRASE_CUTOFF_LEVEL = 7    

def writeLatexRepresentation(csv, ltx, delimiter=","):
    """ returns a latex representation for the given csv file """
    f = open( csv )
    #f.readline() # skip header

    key = itemgetter(0)
    if 'final_assessment' in csv:
        key = itemgetter(1)
        print "***", csv
        delimiter = '\t'

    w = list( sorted(reader(f, delimiter=delimiter), key=key ))[1:]

    # compute and output results
    res = []
    for row in w:
        colName = getColumnName(row)

        # special treatment for the final_assessment csv file
        if 'final_assessment' in csv:
            test_score  = sum( map(float, row[4:7]) )/0.8
            total_score = sum( map(float, row[4:9]) )
            row = [ colName ] +  [ "%d" % test_score, "%d" % total_score, "%.0f" % (float(row[10])*10) ]
        else:
            row = [ colName, ] + [ "%.2f" % float(row[i]) for i in range(2,len(row),2) ]

        res.append( " & ".join( row ) + r"\\" )

    open( path.join( DST_DIRECTORY, ltx), "w" ).write( "\n".join( res ) ) 


#
# Main
# 

# getColumnName = lambda row: RE_NAME.search( row[0] ).group(1).capitalize()
def getColumnName(row):
    try:
        name = row[0] if not row[0].isdigit() else row[1]
        res = RE_NAME.search( name ).group(1).capitalize()
    except AttributeError:
        res =  " ".join(row[0].split("\t")[1:2])

    return res



for csv, ltx in FILES:
    writeLatexRepresentation(csv, ltx)
        

