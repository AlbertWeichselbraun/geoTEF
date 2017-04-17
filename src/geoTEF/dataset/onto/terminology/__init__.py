#!/usr/bin/env python
"""
   @package dataset.onto.terminology
   datatypes used to evaluate an ontology's terminology
"""

# -----------------------------------------------------------------------------------
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

from geoTEF.dataset.types import ILocationReference
from operator import mul, itemgetter
from itertools import chain, izip_longest
from nltk.corpus import wordnet
from eWRT.stat.string import lev, VectorSpaceModel, wordSimilarity, damerauLev, nysiis
from eWRT.util.cache import MemoryCached, DiskCache, DiskCached
from eWRT.ws.wikipedia.distance import WikiDistance
from eWRT.ws.yahoo import Yahoo
from eWRT.stat.coherence import Coherence, DiceCoherence, PMICoherence
from multiprocessing import Pool
from os import getpid

import math
from collections import defaultdict
from nose.plugins.attrib import attr

# logging
from logging import getLogger
log = getLogger(__name__)

# @var 
# number of documents to fetch by the WebDocumentTerm class
WEB_DOCUMENT_COUNT = 10
# @var
# number of context terms to consider for the retrieval of the Web Documents
CONTEXT_TERM_COUNT = 3 

cleanup = lambda s: s.replace(")", "").replace("(","").replace(",", "").replace(".", "").lower()

class OntologyConcept(object):
    """ describes on ontology concept """
    
    def __init__(self, name, context_terms=None):
        self.name = name
        self.context_terms = context_terms
        
    def __str__(self):
        """ String representation of the OntologyConcept. 
            Required by caching to determine whether two objects are identical """
        return "%s %s <%s>" % (self.__class__.__name__, self.name, ", ".join( sorted(self.context_terms)) )
    
    def __repr__(self): return self.__str__()
    
    @staticmethod
    def sequenceToOntologyConceptList(cl):
        """ @param[in] a list of concepts
            @returns a list of OntologyConcepts using all concepts
                     as their context
        """
        return [ OntologyConcept(term, cl) for term in sorted(cl) ]

    @staticmethod
    def statementsToDirectNeighborOntologyConceptList(st):
        """ @param[in] a list of rdf statements (s,p,o)
            @returns a list of OntologyConcepts using 
                     a statement's neighbors as its context
        """
        res = defaultdict( set )
        for s,p,o in st:
            res[s].add(o)

        return [ OntologyConcept(term, tuple(context)) for term, context in res.items() ]

        
    
    @staticmethod
    def getWordConcepts(c):
        """ @param[in] c concept
            @returns a list containing the concepts of the 
                     words c consists of """
        return [OntologyConcept(w, c.context_terms) 
                   for w in c.name.split() ]
        
    @staticmethod
    def wordSimilarity(c1, c2, similarityMeasure):
        """ returns the per word similarity of the given
            concepts (based on the words the concepts is composed of """
        assert isinstance(c1, OntologyConcept)
        assert isinstance(c2, OntologyConcept)
        
        conceptList = list( izip_longest(
                        OntologyConcept.getWordConcepts(c1),
                        OntologyConcept.getWordConcepts(c2),
                        fillvalue = OntologyConcept("") ) )
        c1List, c2List = map(itemgetter(0), conceptList), map(itemgetter(1), conceptList)
        assert( len(c1List) == len(c2List) )
        
        score = float(sum([ max( [ similarityMeasure(w1,w2) for w1 in c1List] ) 
                 for w2 in c2List ])) / len(c1List)
        return score
        
    def getMostProbableWordnetSense(self):
        """ returns the most probable wordnet sense
            for the given concept """
        synsets = wordnet.synsets( self.name )
        if not synsets:
            return None
        return self._disambiguateSynsets(synsets)

    @staticmethod
    @MemoryCached
    def getSynsetDescription(synset):
        """ @param[in] synset  the synset to retrieve the description from """
        getDesc = lambda s: cleanup(s.definition).split(" ") + s.lemma_names
        
        return list( chain( *map( getDesc, [synset]+synset.hypernyms()+synset.hyponyms())) )

        
    def _disambiguateSynsets(self, synsets):
        """ disambiguates a synset based on its context terms
            @param[in] the synsets
            @returns the most probable sense
        """
        v_ref = VectorSpaceModel( [ s.lower for s in self.context_terms] )
        max_sim, max_synset = 0.0, synsets[0]
        for synset in synsets[1:]:
            terms = self.getSynsetDescription(synset) 
            sim = v_ref * VectorSpaceModel( terms )
            if sim>max_sim:
                max_sim, max_synset = sim, synset
        
        return max_synset
            

class TermReference(ILocationReference):
    """ Superclass for all Terminology comparison operations """
    def __init__(self, e):
        ILocationReference.__init__(self)
        assert isinstance(e, OntologyConcept)
        self.e = e 

    def __and__(self, o): raise NotImplementedError

    def __str__(self):
        """ String representation of the concept
            Required by caching to determine whether two objects are identical """
        return "%s <%s>" % (self.__class__.__name__, self.e.name) 

    def __repr__(self): return self.__str__()
 

class EqualTerm(TermReference):
    """ compares whether the terms are equal or not """
    def __and__(self, o):
        assert isinstance(o, TermReference)
        return self.e.name == o.e.name and 1 or 0
        
    def __or__(self, o):
        assert isinstance(o, TermReference)
        return self.e.name == o.e.name and 1 or 0
        
class WikipediaTerm(TermReference):
    
    def __init__(self, e):
        TermReference.__init__(self, e)
        self.d = WikiDistance()
        
    def __or__(self, o):
        if self.e.name == o.e.name:
            return 1.
        return 1. if self.d.isSameAs(self.e.name, o.e.name) or self.d.isSibling(self.e.name, o.e.name) else 0.

        
         
class StringEditTerm(TermReference):
    """ Uses the Damerau Levenshtein distance for evaluating
        the ontology's terminology """
        
    # max. string edit distance to be considered relevant as percentage
    # of the largest term's length
    THRESHOLD = 0.5
        
    def __and__(self, o):
        return self.__or__(o)>0.0 and 1 or 0
        
    def __or__(self, o):
        maxlen = float(max(len(self.e.name), len(o.e.name)))
        u = (1-damerauLev(self.e.name, o.e.name)/maxlen-StringEditTerm.THRESHOLD ) / StringEditTerm.THRESHOLD
        return max( 0.0, u )                 

class PhoneticTerm(TermReference):
    """ compares the terms to each other using phonetic string
        matchin """
        
    THRESHOLD = 0.5

    def __init__(self, e, phonetic_algorithm=nysiis):
        """ @param[in] phonetic_algorithm  Algorithm to compute the 
                                           phonetic string representation
        """
        TermReference.__init__(self, e)
        self.phonetic_algorithm = phonetic_algorithm
    
    def __or__(self, o):
        s1 = self.phonetic_algorithm( self.e.name )
        s2 = self.phonetic_algorithm( o.e.name )
        maxlen = float( max(len(s1), len(s2)) )
        u = (1-lev(s1, s2)/maxlen-StringEditTerm.THRESHOLD ) / StringEditTerm.THRESHOLD
        return max( 0.0, u )                 

class WebDocumentTerm(TermReference):
    """ @class WebDocumentTerm
        Similarity metric based on the similarity of the documents retrieved
        with a web search.
    """

    yahoo = Yahoo()
    __cache__ = DiskCache(".diskCache-WebDocumentTerm-conceptCache", cache_nesting_level=2)

    @staticmethod
    def _getConceptWebDocuments(concept):
        """ returns web documents describing the given concept 
            @param[in] concept concept used to describe the text
        """
        searchTerms = (concept.name,) +tuple(concept.context_terms)[:CONTEXT_TERM_COUNT]
        log.debug("Searching for %s" % str(searchTerms) )
        yq = Yahoo.getSearchResults( \
               WebDocumentTerm.yahoo.query( searchTerms, \
                                            count=WEB_DOCUMENT_COUNT, \
                                            queryParams={'view':'keyterms', 'abstract': 'long', 'type':'html,text'}) )
        
        p = Pool( WEB_DOCUMENT_COUNT )
        text = "\n".join( p.map( p_getWebDocumentText, yq ) )

        return cleanup( text )

    @staticmethod
    def _getConceptWebDocumentsVector(concept):
        return VectorSpaceModel( WebDocumentTerm._getConceptWebDocuments( concept ).split() )

    @staticmethod
    @DiskCached(".diskCache-WebDocumentTerm-or")
    def _or(c1, c2):
        """ Compares two concepts and returns their similarity score
            @param[in] c1 the first OntologyConcept
            @param[in] c2 the second OntologyConcept
            @returns the similarity betwen c1 and c2 
        """
        c1Text = WebDocumentTerm.__cache__.fetchObjectId( c1, WebDocumentTerm._getConceptWebDocumentsVector, c1 )
        c2Text = WebDocumentTerm.__cache__.fetchObjectId( c2, WebDocumentTerm._getConceptWebDocumentsVector, c2 )

        # similarity for concepts with no matches

        if len(c1Text.v) == 0 or len(c2Text.v) == 0:
            if len(c1Text.v) == 0:
                log.warn("No web pages found for '%s'" % c1)
            if len(c2Text.v) == 0:
                log.warn("No web pages found for '%s'" % c2)
            return 0.

        return c1Text * c2Text
        
    def __or__(self, o):
        return self._or(self.e, o.e)


class GoogleDistanceTerm(TermReference):

    def __or__(self, o):
        """ google distance """
        y = PMICoherence( dataSource = Yahoo() )
        c = y.getTermCoherence(self.e.name, o.e.name)
        return c if c else 0.


class WordNetTerm(TermReference):
    """ uses wordnet for evaluating the terminology """
    
    def __init__(self, e, similarity_measure='path_similarity'):
        # similarity measure to use 
        #(path_similarity, wup_similarity)
        TermReference.__init__(self, e)
        self.similarity_measure   = similarity_measure
    
    # threashold
    similarity_threshold = 0.5 
    
   
    def __and__(self, o):
        return self._wordnetSimilarity(self.e, o.e)
       
    def _wordnetSimilarity(self, c1, c2):
        """ computes the wordnet similarity between two concepts """
        if c1.name == c2.name:
            return 1.0

        try:
            w1 = c1.getMostProbableWordnetSense()
            w2 = c2.getMostProbableWordnetSense()
            if w1 is None or w2 is None:     
                return 0.
            else:
                # the similarity metric yields None, if the two synsets are
                # not compatbile (e.g. comparing an adjective to a noun.
                return w1.__getattribute__(self.similarity_measure)(w2) or 0.0

        except:
            # return 0. if the computation did not work out
            log.error("Cannot compute wordnet senses/similarity for '%s' and '%s'" % (c1, c2) )
            return 0.
    
    def __or__(self, o):
        return OntologyConcept.wordSimilarity(self.e, o.e, self._wordnetSimilarity)


class OntologyTerm(TermReference):
    """ combines all measures yielding an ontology based metric """

    METRICS = (EqualTerm, StringEditTerm, PhoneticTerm, WordNetTerm, WikipediaTerm, WebDocumentTerm, GoogleDistanceTerm )

    def __init__(self, e):
        """ @param[in] lm A list of TermReference metrics to use in the ontology metric """
        TermReference.__init__(self, e)
        self.metrics = dict( [ (m(e), DiskCache(".diskCache-single-%s" % m.__name__)) for m in self.METRICS ] )
        

    def __or__(self, o):
        return max( [  cache.fetchObjectId( (o.e, self.e), metric.__or__, o)  \
             for metric, cache in self.metrics.items()  ] )

    
# --------------------------------------------------------------------------------
# 
# UNITTESTING
#   
# --------------------------------------------------------------------------------

class TestOntologyConcepts(object):

    o1 = OntologyConcept("space", ("galaxy", "earth", "universe", "atmosphere", "unlimited"))
    o2 = OntologyConcept("human", ("man", "woman", "child"))

    def testDisambiguation(self):
        s = self.o1.getMostProbableWordnetSense()
        print s, s.lemma_names, s.definition
        assert s == wordnet.synsets("space")[0]

    @attr("remote")
    def testGoogleDistanceTerm(self):
        """ test the google distance metric """
        d = GoogleDistanceTerm(self.o1) | GoogleDistanceTerm(self.o2)
        print d
        assert d>0. and d<1.

    def testToString(self):
        """ tests the OntologyConcept's string representation """
        print self.o2
        assert str(self.o2) == "OntologyConcept human <child, man, woman>"

    def testStatementsToDirectNeighborOntologyConceptList(self):
        """ tests the transformation from statements to ontology concepts """
        st =  [ (1,0,2), (1,0,3), (2,0,4), (2,0,5), (3,0,5), (3,0,7), (3,0,8) ]
        ontologyConceptList = OntologyConcept.statementsToDirectNeighborOntologyConceptList( st )
        assert len(ontologyConceptList) == 3

        for oc in ontologyConceptList:
            if oc.name == 1:
                assert len(oc.context_terms) == 2
                assert 2 in oc.context_terms
                assert 3 in oc.context_terms
            elif oc.name == 2:
                assert len(oc.context_terms) == 2
                assert 4 in oc.context_terms
                assert 5 in oc.context_terms
            elif oc.name == 3:
                assert len(oc.context_terms) == 3
                assert 5 in oc.context_terms
                assert 7 in oc.context_terms
                assert 8 in oc.context_terms

    
class TestTermReference(object):
    
    TERMS = { 'ana'  : OntologyConcept('ana'), 
              'anna': OntologyConcept('anna'),
              'anton': OntologyConcept('anton')
            }
    
    def testStringEditTerm(self):
        t = lambda x: StringEditTerm(TestTermReference.TERMS[x])
        assert t('ana') & t('anton') == 0
        assert t('ana') & t('anna') == 1

        assert t('ana') | t('anna') == 0.5

class TestMultiProcessing(object):
    """ @class TestMultiProcessing
    """
    TEST_CONCEPTS = ( OntologyConcept("cpu", ('computer', )),
                      OntologyConcept("central processing unit", ('computer', ) ),
                      OntologyConcept("austria", ('country, ', 'europe', )),
                      OntologyConcept("microsoft", ('computer', 'company') ),
                      OntologyConcept("microsoft inc.", ('computer', 'company')),
                      OntologyConcept("google", ('computer', 'company')),
                    )

    getConceptPairs = staticmethod( \
          lambda x: [ (x(a), x(b)) for a,b in zip(TestMultiProcessing.TEST_CONCEPTS[:-1], 
                                                  TestMultiProcessing.TEST_CONCEPTS[1:]) ] )

    def __init__(self):
        from multiprocessing import Pool
        self.p = Pool(4)

    def testToString(self):
        c1 = TestMultiProcessing.TEST_CONCEPTS[0]
        c2 = OntologyConcept("cpu", ("computer", ))
        assert str(c1) == str(c2)

    @attr("remote")
    def testWikipediaMultiProcessing(self):
        """ wikipedia """
        conceptPairs = self.getConceptPairs( WikipediaTerm )
        self.p.map( t_compare, conceptPairs )

    @attr("slow")
    @attr("remote")
    def testWebDocumentTermEmptyPages(self):
        """ tests for empty pages (yahoo! reported that no pages have been 
            found for the terms above; which is obviously false"""
        o1 = WebDocumentTerm( OntologyConcept("contractors", ("communication", ) ) )
        o2 = WebDocumentTerm( OntologyConcept("poor time management", ("increase")))

        from sys import stderr as out
        c1 = WebDocumentTerm._getConceptWebDocumentsVector(o1.e)
        assert len(c1.v) > 100

        c2 = WebDocumentTerm._getConceptWebDocumentsVector(o2.e)
        assert len(c2.v) > 100

        print o1 | o2 


    @attr("remote")
    def testGoogleDistanceTerm(self):
        """" tests google distance term """
        conceptPairs = self.getConceptPairs( GoogleDistanceTerm )
        self.p.map( t_compare, conceptPairs )

#  --------------------------------------------------------------------------------
# 
# MULTIPROCESSING FUNCTIONS
#   
# --------------------------------------------------------------------------------

def p_getWebDocumentText(yObj):
    """ 
        @param[in] yObj Yahoo! search result object
        @returns the text of the given result page

        @remarks
        Used by WebDocumentTerm._getConceptWebDocuments
    """
    with open("/tmp/getPageText-%s.log" % getpid(), "a") as f:
        f.write("Retrieving %s.\n" % yObj.search_result['url'])
        f.flush()
        pageText = yObj.getPageText()
        f.write("Done retrieving %s.\n" % yObj.search_result['url'])
        f.flush()
    return pageText

def t_compare(c):
    """ 
        @params[in] c ... a tuple containing the concepts to compare

        @remarks
        used by the test*MultiProcessing unit tests
    """
    return c[0] | c[1]


