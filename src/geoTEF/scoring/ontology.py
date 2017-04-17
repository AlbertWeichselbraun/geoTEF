#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
   @package scoring.ontology
   ontology scoring
   [1] concepts
   [2] relations
   [3] hierarchy
"""

# -----------------------------------------------------------------------------------
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
__revision__ = "$Id$"

from geoTEF.dataset.onto.terminology import OntologyConcept
from geoTEF.dataset.onto.terminology import EqualTerm, StringEditTerm, WordNetTerm
from multiprocessing import Pool, cpu_count

# logging
from logging import getLogger
log = getLogger(__name__)

DEFAULT_POOL_SIZE = 2*cpu_count()


class ConceptScoring(object):
    """ Compares Ontology Concepts to each other """

    __slots__ = ('resultConceptScoringSet', 'referenceConceptScoringSet', 'scoringFunction', 'score', 'pool', )

    def __init__(self, resultConceptSet, referenceConceptSet, ilr, scoringFunction = "&", poolSize=DEFAULT_POOL_SIZE):
        """
        @param[in]  resultConceptSet    set of concepts
        @param[in]  referenceConceptSet set of concepts
        @param[in]  ilr                 class for comparing concepts with each other
        @param[in]  scoringFunction     either (&...binary, or | scalar)
        @param[in]  poolSize            number of pools to use for the computations
        """
        self.resultConceptScoringSet    = [ ilr(r) for r in resultConceptSet ]
        self.referenceConceptScoringSet = [ ilr(r) for r in referenceConceptSet ]
        self.scoringFunction = scoringFunction
        if poolSize == 1:
            self.score = self.sp_score
            log.debug("Applying singleprocessing scoring for %s." % ilr.__name__ )
        else:
            self.pool = Pool( poolSize )
            self.score = self.mp_score
            log.debug("Applying multiprocessing scoring with %d pools for %s." % (poolSize, ilr.__name__) )

        
    def sp_score(self):
        """ returns a similarity score for the given concept lists 

            @remarks
            single processing version.
        """
        scoringFormular = "res %s ref" % self.scoringFunction
        s = sum( [ max( [ eval(scoringFormular) for res in self.resultConceptScoringSet ] ) 
                for ref in self.referenceConceptScoringSet ] )
        return s

       
    def mp_score(self):
        """ returns a similarity score for the given concept lists

            @remarks
            multi processing version.
        """
        if not self.resultConceptScoringSet or not self.referenceConceptScoringSet:
            return 0.
        scoringFormular = "res %s ref" % self.scoringFunction
        s = sum( [ max( self.pool.map(p_score, [(scoringFormular, res, ref) for res in list(self.resultConceptScoringSet) ]) ) 
                for ref in self.referenceConceptScoringSet ] )
        return s
    
def p_score(currentTaskParameters):
    """ scoring function used by the multiprocessing pool """
    scoringFormular, res, ref = currentTaskParameters
    log.debug("Scoring %s|%s" % (res,ref) )
    return eval(scoringFormular)
        
        
# UNITTESTS :-)

class TestConceptScoring(object):
    
    resultTerms = set( ('computer', 'love', 'human') )
    referenceTerms  = set ( ('computer', 'like', 'man') )
    
    def __init__(self):
        """ create ontology concepts """
        self.resultConcepts    = OntologyConcept.sequenceToOntologyConceptList(self.resultTerms)
        self.referenceConcepts = OntologyConcept.sequenceToOntologyConceptList(self.referenceTerms)  
        
    @staticmethod
    def _to_ontology_concept(st):
        """ converts a sequence of terms to a sequence of ontology concepts """
        return [ OntologyConcept(term, st) for term in st ]
    
    def testMultiprocessingScorings(self):
        """ test different scoring methods """
        for scoringMethod in ( EqualTerm, StringEditTerm, WordNetTerm ):
            c = ConceptScoring(self.resultConcepts, self.referenceConcepts, scoringMethod, "|")
            print scoringMethod.__name__, "\t", c.score()


    def testSingleprocessingScorings(self):
        """ test different scoring methods """
        for scoringMethod in ( EqualTerm, StringEditTerm, WordNetTerm ):
            c = ConceptScoring(self.resultConcepts, self.referenceConcepts, scoringMethod, "|", poolSize=1)
            print scoringMethod.__name__, "\t", c.score()
            
