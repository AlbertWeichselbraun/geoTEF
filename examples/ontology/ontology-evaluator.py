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

import os.path
from eWRT.input.conv.cxl import XCL2RDF
from eWRT.util.profile import profile
from eWRT.util.cache import DiskCache
from eWRT.stat.eval import metrics

# coherence
from eWRT.stat.coherence import Coherence, DiceCoherence, PMICoherence
from eWRT.ontology.eval.terminology import CoherenceEvaluator
from eWRT.ws.yahoo import Yahoo
from eWRT.ws.delicious import Delicious


from geoTEF.scoring.ontology import ConceptScoring
from geoTEF.dataset.onto.terminology import OntologyConcept, EqualTerm, StringEditTerm, WordNetTerm, PhoneticTerm, WikipediaTerm, OntologyTerm, WebDocumentTerm, GoogleDistanceTerm
from geoTEF.dataset.onto.relationtypes import EqualRel, EqualGroup, SimilarGroup

from rdflib.Graph import Graph
from rdflib import Namespace, Literal

from os import path
from shutil import rmtree
from operator import itemgetter
from glob import glob
from csv import writer
from bz2 import BZ2File

# ontology cleanup
from eWRT.input.clean.text import *
from eWRT.stat.string.spelling import SpellSuggestion

# logging
import logging
logging.basicConfig(filename="/tmp/evaluator.log", filemode="w", level=logging.DEBUG)
log = logging.getLogger("geoTEF.examples.ontology.evaluator")

NS_RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
NS_WL   = Namespace("http://www.weblyzard.com/2005/03/31/wl#")

SOURCE_DIR = "./source"
RESULT_DIR = "./result"
CUSTOM_RISK_CORPUS = "risk-corpus.text.bz2"
PMI_CUTOFF_LEVEL   = 0.5

# compile customized spelling suggestions
s = SpellSuggestion()
s.verbose=True
s.train( SpellSuggestion.words( BZ2File( CUSTOM_RISK_CORPUS ).read() ) )

# compile cleanup queue

cleanXA = lambda x: x.replace("&#xa;", " ") # cleans up unicode characters used in the concept names

strCleanupPipe = (unicode.lower, cleanXA, RemovePossessive(), FixDashSpace() )
phrCleanupPipe = (SplitEnumerations(), SplitMultiTerms(), SplitBracketExplanations() )
wrdCleanupPipe = (FixSpelling(), RemovePunctationAndBrackets(),)
phraseCleanup = PhraseCleanup(strCleanupPipe, phrCleanupPipe, wrdCleanupPipe )


def extractSPO(rdfOntology):
    """ extracts a set of all relations present in the given ontology
        @param[in] rdfOntology    the rdflib.Graph object representing the ontology
        @returns a set of all triples present in the given ontology 
    """
    q = "SELECT ?s ?p ?o WHERE { ?cs ?cp ?co. ?cs rdfs:label ?s. ?co rdfs:label ?o. ?cp rdfs:label ?p. }"
    rel = set()
    for ss, pp, oo in rdfOntology.query( q, initNs=dict(rdfs=NS_RDFS, wl=NS_WL) ):
        rel = rel.union( [ (s, p, o) for s in phraseCleanup.clean(ss) for p in phraseCleanup.clean(pp) for o in phraseCleanup.clean(oo) ] )
    return rel 

def extractConceptSet(rdfOntology):
    """ extracts a set of all concepts present in the given ontology
        @param[in] rdfOntology    the rdflib.Graph object representing the ontology
        @returns a set of all concepts present in the given ontology 
    """
    concepts = set()
    concepts = concepts.union( [ s for s, p, o in extractSPO(rdfOntology) ] )
    concepts = concepts.union( [ o for s, p, o in extractSPO(rdfOntology) ] )
    return concepts

def extractRelationSet(rdfOntology):
    """ extracts a set of all relations present in the given ontology
        @param[in] rdfOntology    the rdflib.Graph object representing the ontology
        @returns a set of all relations present in the given ontology 
    """
    return set( [ p for s, p, o in extractSPO(rdfOntology) ] )

def conceptTermCount( rdfOntology ):
    """ returns true if the ontology contains sentence concepts  which we
        cannot evaluate using terminology related measures
    """
    return max( [ len(c) for c in extractConceptSet(rdfOntology) ] )

def _get_scoring_method(res, ref, ilrString, mode):
    """ returns the scoring method used to perfrom the scoring """
    if mode == 'or':
        return ConceptScoring(res, ref, eval(ilrString), '|')
    else:
        return ConceptScoring(res, ref, eval(ilrString))


def _readOntology( fname ):
    """ reads the given ontology using the correct 
        format 
        @param[in] the ontology's file name
        @returns the ontology graph
    """
    if fname.endswith(".cxl"):
        return XCL2RDF.toRDF( open( fname ).read() )
    elif fname.endswith(".rdf") or fname.endswith(".xml"):
        g = Graph()
        g.parse( fname, "xml" )
        return g
    else:
        raise "Unknown Ontology format error"


        
def evalOntology( fname, fGoldStd, methodLabel, method ):
    """ evaluates the given ontology and writes the results into a file 
    @param[in] fname        file name of the ontology to evaluate
    @param[in] fGoldStd     file name of the gold standard ontology
    @param[in] methodLabel  label of the method used in the evaluation
    @param[in] method       method used in the evaluator
    """
    
    goldStd  = _readOntology( fGoldStd )
    ontology = _readOntology( fname )

    goldStdConcepts  = OntologyConcept.sequenceToOntologyConceptList(extractConceptSet(goldStd))
    ontologyConcepts = OntologyConcept.sequenceToOntologyConceptList(extractConceptSet(ontology))

    log.info("Comparing the ontology concepts %s to the gold standard %s." % (ontologyConcepts, goldStdConcepts))

    res = [ conceptTermCount( ontology ) ]
    for scoringMethod in (EqualTerm, StringEditTerm, PhoneticTerm, WordNetTerm, WikipediaTerm, WebDocumentTerm, GoogleDistanceTerm, OntologyTerm, ):
        __cache__ = DiskCache(".diskCache-%s-%s" % (scoringMethod.__name__, os.path.basename(fGoldStd)) )
        # Methods using neighbor concepts
        if scoringMethod in (WebDocumentTerm, ):
            goldNeighborConcepts = OntologyConcept.statementsToDirectNeighborOntologyConceptList( extractSPO(goldStd) )
            ontoNeighborConcepts = OntologyConcept.statementsToDirectNeighborOntologyConceptList( extractSPO(ontology) )
            c = ConceptScoring(ontoNeighborConcepts, goldNeighborConcepts, scoringMethod, '|', poolSize=1)
            key = "%s, %s |" % (ontoNeighborConcepts, goldNeighborConcepts)

        # methods using all concepts
        else:
            ps = 1 if scoringMethod == OntologyTerm else 4
            c = ConceptScoring(ontologyConcepts, goldStdConcepts, scoringMethod, '|', poolSize=ps)
            key = "%s, %s |" % (ontologyConcepts, goldStdConcepts)

        score = __cache__.fetchObjectId(key, c.score)
        print scoringMethod, score
        res.append(score)
        # compute precision and recall
        p = float(score) / len(ontologyConcepts)
        r = float(score) / len(goldStdConcepts)
        if p==0. and r== 0.:
            res.append(0.)
        else:
            res.append( metrics.fMeasure(p,r) )

    return res

def evalRelationTypes(fname, fGoldStd, methodLabel, method ):
    """ evaluates the given ontology and writes the results into a file 
    @param[in] fname        file name of the ontology to evaluate
    @param[in] fGoldStd     file name of the gold standard ontology
    @param[in] methodLabel  label of the method used in the evaluation
    @param[in] method       method used in the evaluator
    """
    goldStd  = _readOntology( fGoldStd )
    ontology = _readOntology( fname )

    goldStdConcepts  = set(map(str, extractRelationSet(goldStd)))
    ontologyConcepts = set(map(str, extractRelationSet(ontology)))

    log.info("Comparing the relation set %s to the gold standard %s." % (ontologyConcepts, goldStdConcepts))

    res = [ 1 ]
    for scoringMethod in (EqualRel, EqualGroup, SimilarGroup):
        __cache__ = DiskCache(".diskCache-%s-%s" % (scoringMethod.__name__, os.path.basename(fGoldStd)) )
        c = ConceptScoring(ontologyConcepts, goldStdConcepts, scoringMethod, '|')
        key = "%s, %s |" % (ontologyConcepts, goldStdConcepts)
        score = __cache__.fetchObjectId(key, c.score)
        res.append(score)
        # compute precision and recall
        p = float(score) / len(ontologyConcepts)
        r = float(score) / len(goldStdConcepts)
        if p==0. and r== 0.:
            res.append(0.)
        else:
            res.append( metrics.fMeasure(p,r) )

    #print ">>>", len(goldStdConcepts), len(ontologyConcepts), "***", res
    return res

def evalCoherence(fname, fGoldStd, methodLabel, method ):
    """ evaluates the given ontology and writes the results into a file 
    @param[in] fname        file name of the ontology to evaluate
    @param[in] fGoldStd     file name of the gold standard ontology
    @param[in] methodLabel  label of the method used in the evaluation
    @param[in] method       method used in the evaluator
    """
    # goldStd  = _readOntology( fGoldStd )
    ontology = _readOntology( fname )
    ontologyRelations = extractSPO( ontology )

    res = [ conceptTermCount( ontology ) ]
    for coherenceLabel, coherenceMethod in ( ('PMI (Yahoo)', DiceCoherence( dataSource=Yahoo() )),
                                             ('PMI (Delicious)', PMICoherence( dataSource=Delicious() )) ):

        if 'Delicious' in coherenceLabel:
            continue

        statementEvalResult = [ (coherenceMethod.getTermCoherence(s,o), s,p,o) for s,p,o in ontologyRelations ] 
        strongStatements    = [ (sig, s,p,o) for sig, s,p,o in statementEvalResult if sig >= PMI_CUTOFF_LEVEL ]
        res.append( float(len(strongStatements))/len(statementEvalResult) )
        res.append( len(strongStatements) )
        #res.append( "%s/%s" % (len(strongStatements),len(statementEvalResult)) )

    return res


# 
# main
#

def serializeEvaluation(fname, evalHeader, evalFunction):
    """ performes and writes the given evaluation """
    if False:
        fGoldStdList = glob("./source/gold-standard/*.cxl")
    else:
        fGoldStdList = glob("./source/gold-standard/*.rdf")

    for fGoldStd in fGoldStdList:
        goldStdName = os.path.splitext( os.path.basename( fGoldStd ) )[0]
        print "**********************************************"
        print "*** Analyzing: "
        print "***", goldStdName
        print "**********************************************"
        f = open("%s_%s.csv" % (fname, goldStdName) , "w")
        w = writer(f)
        w.writerow( evalHeader )

        for no, fname in enumerate( glob("./source/*.cxl") ):
            w.writerow( [ path.basename(fname)] +evalFunction( fname, fGoldStd, "testMethod", "test" ) )
            f.flush()
            
        f.close()


def runTerminologyEvaluator():
    """ main function """
    serializeEvaluation("terminology", ('ontology,', 'sentence Concepts', 'Equal', 'StringEdit', 'Phonetic', 'WordNet', 'Wikipedia Click Distance', 'WebDocumentTerm', 'Yahoo distance', 'Ontology', ), evalOntology)

def runRelationTypeEvaluator():
    """ compares the relations types """
    serializeEvaluation("relation-types", ('ontology', 'sentence concepts', 'Equal', 'EqualGroup', 'SimilarGroup', ), evalRelationTypes )

def runCoherenceEvaluator():
    """ compares the relations types """
    serializeEvaluation("coherence", ('ontology', 'sentence Concepts', 'Dice (Yahoo)', 'Dice (...)', ), evalCoherence )


        

if __name__ == '__main__':
    runTerminologyEvaluator()
    runRelationTypeEvaluator()
    runCoherenceEvaluator()
    
