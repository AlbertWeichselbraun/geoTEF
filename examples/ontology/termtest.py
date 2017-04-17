#!/usr/bin/env python
"""
  ontology-evaluator.py
  evaluates an ontology using the geoTEF framework
"""
# -----------------------------------------------------------------------------------
# ontology-evaluator.py
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

from glob import glob
from bz2 import BZ2File
from eWRT.input.conv.cxl import XCL2RDF
from rdflib import Namespace

from eWRT.input.clean.text import *
from eWRT.stat.string.spelling import SpellSuggestion

import logging
logging.basicConfig(filename="/tmp/termtest.log",level=logging.DEBUG)
log = logging.getLogger("geoTEF.examples.ontology.termTest")

NS_RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
NS_WL   = Namespace("http://www.weblyzard.com/2005/03/31/wl#")

SOURCE_DIR         = "./source"
RESULT_DIR         = "./result"
CUSTOM_RISK_CORPUS = "risk-corpus.text.bz2"

# basic concept cleanup
cleanup = lambda c: " ".join(c.replace("'s", "").split() ).lower()

# compile customized spelling suggestions
s = SpellSuggestion()
s.verbose=True
s.train( SpellSuggestion.words( BZ2File( CUSTOM_RISK_CORPUS ).read() ) )

# compile cleanup queue

strCleanupPipe = (unicode.lower, RemovePossessive(), FixDashSpace() )
phrCleanupPipe = (SplitEnumerations(), SplitMultiTerms(), SplitBracketExplanations() )
wrdCleanupPipe = (FixSpelling(), RemovePunctationAndBrackets(),)
phraseCleanup = PhraseCleanup(strCleanupPipe, phrCleanupPipe, wrdCleanupPipe )

def extractConceptSet(rdfOntology):
    """ extracts a set of all concepts present in the given ontology
        @param[in] rdfOntology    the rdflib.Graph object representing the ontology
        @returns a set of all concepts present in the given ontology 
    """
    concepts = set()
    q = "SELECT ?s ?p ?o WHERE { ?cs ?cp ?co. ?cs rdfs:label ?s. ?co rdfs:label ?o. ?cp rdfs:label ?p. }"
    for s, p, o in rdfOntology.query( q, initNs=dict(rdfs=NS_RDFS, wl=NS_WL) ):
        concepts.add( cleanup(s) )
        concepts.add( cleanup(o) ) 
    return concepts


        
def getConcepts( fname ):
    """ evaluates the given ontology and writes the results into a file 
    @param[in] fname        file name of the ontology to evaluate
    """
    
    goldStd  = XCL2RDF.toRDF( open(fname).read() )
    goldStdConcepts  = extractConceptSet(goldStd)

    result = []
    for concept in goldStdConcepts:
        cleaned_phrase = phraseCleanup.clean( concept )
        if ", ".join(cleaned_phrase) != concept:
            log.info("Replacing '%s' with '%s'" % (concept, ", ".join(cleaned_phrase)) )
        result.extend( cleaned_phrase  )

    return result

# 
# main
#

if __name__ == '__main__':
    s = set()
    for no, fname in enumerate( glob("./source/*.cxl") ):
        s = s.union( set(getConcepts(fname) ) )

    f=open("concepts.awi", "w")
    for c in sorted(s):
        f.write("%s\n" % c)
    f.close()


