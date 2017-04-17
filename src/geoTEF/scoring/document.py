#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
   @package scoring.document
   scores IResultCollection based on different scoring functions
"""

# -----------------------------------------------------------------------------------
# (C)opyrights 2008-2009 by Albert Weichselbraun <albert.weichselbraun@wu.ac.at>
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

from operator import itemgetter
from os import getpid
from sys import stderr, exit
from time import time
from eWRT.config import GEO_ENTITY_SEPARATOR
from eWRT.ws.geonames import GeoEntity
from itertools import groupby
from nose.plugins.attrib import attr
from cPickle import dump

# unittests
from geoTEF.input import CSVResultCollection, SigCSVResultCollection
from StringIO import StringIO


try:
    import psyco
    psyco.full()
except ImportError:
    pass

getContinent = lambda g: g.entityDict['geoUrl'].split(GEO_ENTITY_SEPARATOR,1)[0]
def getCountry(g):
    d = g.entityDict['geoUrl'].split(GEO_ENTITY_SEPARATOR,2)
    return len(d)<2 and d[0] or d[1]

class IScoring(object):

    def __init__(self, resultSet, referenceSet, ilr, scoringFunction = "&" ):
        """ @param[in] scoringFunction (& for binary scoring; | for scalar scoring)
        """
        self.name = resultSet.name
        self.res  = resultSet.data
        self.ref  = referenceSet.data
        self.keys = resultSet.data.keys()
        self.ilr  = ilr
        self.scoringFunction = scoringFunction
        self.pid  = getpid()  # debugging
        

    def __iter__(self): return self

    def next(self, curKey=None):
        """ returns the score from the next document """
        if curKey == None:
            if not self.keys:
                raise StopIteration

            curKey = self.keys.pop()

        # stderr.write("Processing (#%s@%s) %s; %s entries left\n" % (self.pid, time(), curKey,len(self.keys)) )
        self.curKey = curKey
        # check whether both - result and reference set - contain the given key - otherwise assign a score of zero
        if not (curKey in self.ref and curKey in self.res):
            return 0.0

        res = [ self.ilr(g[1]) for g in self.normalizeResultListSize( self.res[curKey], self.ref[curKey] ) ]
        ref = [ self.ilr(g[1]) for g in set(self.ref[curKey]) ] 
        return self.score( res, ref )


    def normalizeResultListSize(self, result, ref):
        """ Determines which items of the result set to include in the evaluation.
            @remark this function was used by the MaxMatchDocumentScoring to get equal
                    size result and reference lists.

            @param[in] result  ... the current (full) result set
            @param[in] ref     ... the reference set
            @returns the resultlist to consider in the evaluation
        """
        raise NotImplementedError
 

    def score(self, result, reference):
        """ returns a score based on the two sets s1, s2
            @param[in] result    ... A list of tags
            @param[in] reference ... A list of reference tags
        """
        raise NotImplementedError


class MaxMatchDocumentScoring(IScoring):
    """ this class provides results and reference set and assigns 
        for every reference entity the score yielded by the highest scoring counterpart.
        (counterparts might be used multiple times).

        e.g. result   : eu/at, eu/de
             reference: eu/at/Vienna, eu/at/Graz, eu/de 
             score    : u(eu/at, eu/at/Vienna) + u(eu/at, eu/at/Graz) + u(eu/de, eu/de) 
    """

    def normalizeResultListSize(self, result, ref):
        """ Determines which items of the result set to include in the evaluation.
            @remark this function creates for MaxMatchDocumentScoring a result list
                    with the same size (or smaller) as the reference list.

            @param[in] result  ... the current (full) result set
            @param[in] ref     ... the reference set
            @returns the resultlist to consider in the evaluation
        """
        size = len( set(ref) )
        return list( sorted(result) )[-size:]


    def score(self, result, reference):
        scoringFormular = "res %s ref" % self.scoringFunction

        score = [ max( [ eval(scoringFormular) for ref in reference ] ) for res in result ]
        return sum( score )


class P1DocumentScoring(IScoring):
    """ this class provides the P@1 score.
        e.g. result   : eu/at, eu/de
             reference: eu/at/Vienna, eu/at/Graz, eu/de 
             score    : max( u(eu/at, eu/at/Vienna), u(eu/at, eu/at/Graz), u(eu/at, eu/de), u(eu/de, eu/at/Vienna), ... )
    """
    def normalizeResultListSize(self, result, ref):
        """ Determines which items of the result set to include in the evaluation.
            @remark returns the _one_ location chosen as focus for the P1DocumentScoring

            @param[in] result  ... the current (full) result set
            @param[in] ref     ... the reference set
            @returns the resultlist to consider in the evaluation
        """
        return list( sorted(result) )[-1:]  


    def score(self, result, reference):
        scoringFormular = "res %s ref" % self.scoringFunction

        score = [ max( [ eval(scoringFormular) for ref in reference ] ) for res in result ]
        return max(score)



class DocumentScoring(IScoring):
    """ this class creates combinations of results and reference set and provides the 
        maximum score based on these combinations

        e.g. result   : eu/at
             reference: eu/at/Vienna, eu/at/Graz, eu/de 
             score    : u(eu/at, eu/at/Vienna) or u(eu/at, eu/at/Graz)
    """

    def score(self, result, reference):
        result      = set(result)
        reference   = set(reference)

        result, reference, total_score  = self.scoreCorrectItems( result, reference )
        total_score += self.scorePartiallyCorrectItems( result, reference, self.scoringFunction )
        return total_score


    @staticmethod
    def scoreCorrectItems(result, reference):
        """ returns the score for correctly identified items
            @param[in] result
            @param[in] reference
            @returns the score obtained from 100% correctly identified 
                     items + the result sets without these items
        """
        correct   = result.intersection(reference)
        result    = result.difference(correct)
        reference = reference.difference(correct)
        return result, reference, len(correct)

    @staticmethod
    def groupItems(lst, groupingFunction):
        """ returns a dictionary of GeoEntities grouped by the
            continent
            @param[in] lst of GeoEntities
            @param[in] groupingFunction function used to group the results
            @returns {'eu': (a,b,c), 'af': (d,e,f), ...}
        """
        expanded_entries = [ (groupingFunction(g.g), g) for g in lst ]
        return [ (k, map(itemgetter(1),v)) for k, v in groupby( sorted(expanded_entries), key=itemgetter(0) ) ]


    def _serializePartialResult(self, result, reference, scoringFunction):
        """ serializes the given data for further inspection 
            (currently used to serialize results with more than 8 elements """
        f = open( "%s-%s-%s.dump" % (self.name, self.curKey, self.ilr.__name__), "w")
        dump( (result, reference, scoringFunction), f )
        f.close()


    def scorePartiallyCorrectItems(self, result, reference, scoringFunction, groupingFunction=getContinent):
        if not result or not reference:
            return 0.0

        resultGrp    = dict( DocumentScoring.groupItems( result, groupingFunction ))
        referenceGrp = DocumentScoring.groupItems( reference, groupingFunction )

        score = 0
        for group, ref in referenceGrp:
            if not group in resultGrp:
                continue
            res = resultGrp[group]

            if len(res)>5 and len(ref)>5:
                print "** WARNING Scoring more than five (%d) different combinations." % len(res)

            # score all groups with more than 8 entries using the country level
            if len(res)>6 and len (ref)>6:
                # this assertion assures that we do not score on the country level twice
                if groupingFunction != getContinent:
                    print "Giving up", groupingFunction, groupingFunction.__name__
                    self._serializePartialResult(result, reference, scoringFunction)
                assert groupingFunction == getContinent
                score += self.scorePartiallyCorrectItems(res, ref, scoringFunction, groupingFunction=getCountry)
            else:
                if res>ref:
                    validResults = DocumentScoring.generateCombinations(list(res), list(ref))
                else:
                    validResults = DocumentScoring.generateCombinations(list(ref), list(res))

                scoringFormular = "x %s y" % scoringFunction
                scorePerCombination = [ sum([eval(scoringFormular) for x, y in res ]) \
                                         for res in validResults ]

                score += max(scorePerCombination)

        return score
            

    @staticmethod
    def generateCombinations( left, right=[] ):
        """ generates all possible combinations of the sets
            e.g. (A,B,C), (1,2,3) => (A1,B2,C3), (A1,B3,C2), ...
        """
        current = left.pop()
        if left:
            res = []
            for r in right:
                snippets = DocumentScoring.generateCombinations(left[:], right)
                for snippet in snippets:
                    snippet.append( (current, r) )
                    res.append( snippet )
            return DocumentScoring.removeInvalidCombinations( res )

        else:
            return [ [ (current, r) ] for r in right ]


    @staticmethod
    def removeInvalidCombinations( combis ):
        """ removes all combinations, which contain invalid
            tuples, such as (A1,B1,C1) 
            @param[in] all generated combinations
            @returns a list of valid combinations
        """
        res = [ c for c in combis \
                    if len( set(map(itemgetter(0), c) ) ) == len(c) and \
                       len( set(map(itemgetter(1), c) ) ) == len(c) ]

        return res or combis

        
class TestDocumentScoring(object):
    def __init__(self):
        g = lambda x: GeoEntity.factory( id=x )[0]
        self.EXAMPLE_ENTITIES = { '.ch'       : g(2658434),
                                  '.at'       : g(2782113),
                                  '.carinthia': g(2774686),
                                  '.eu'       : g(6255148),
                                  'villach'   : g(2762372),
                                  'hermagor'  : g(2776497),
                                  'serbia'    : g(6290252),
                                  'montenegro': g(863038),
                       }

    @attr("remote")
    def testGetCountry(self):
        """ tests whether testGetCountry works """
        print getCountry(self.EXAMPLE_ENTITIES['.at'])
        print getCountry(self.EXAMPLE_ENTITIES['.eu'])

        assert getCountry(self.EXAMPLE_ENTITIES['.at']) == "Republic of Austria"
        assert getCountry(self.EXAMPLE_ENTITIES['.eu']) == "Europe"

    def testGenerateCombinations(self):
        """ tests the generation of combinations """
        a = [ 'a', 'b', 'c' ]
        b = [1, 2, 3]
        expected_result = ( [('a',1), ('b', 2), ('c', 3)],
                            [('a',1), ('b', 3), ('c', 2)],
                            [('a',2), ('b', 1), ('c', 3)],
                            [('a',2), ('b', 3), ('c', 1)],
                            [('a',3), ('b', 1), ('c', 2)],
                            [('a',3), ('b', 2), ('c', 1)],
                          )
        d = DocumentScoring.generateCombinations( a, b )
        assert len(d) == len(expected_result)
        for r in expected_result:
            assert r in d

    @attr("slow")
    def testLargeCombinations(self):
        a = range(5)
        b = range(5)
        #b = list("abc")
        c = DocumentScoring.generateCombinations(a,b) 

    def testGenerateCombinationsExtrema(self):
        """ tests the algorithm in extreme settings """
        a = ['a']
        b = [ 1 ]
        d = DocumentScoring.generateCombinations( a, b )
        assert d == [[('a', 1)]]

        v = DocumentScoring.removeInvalidCombinations(d)
        print "xxx", v
        assert v == [[('a', 1)]]


class TestFileBasedDocumentScoring(object):
        
    reuters = StringIO("""46274,2077456,AUSTRALIA,Oceania>Commonwealth of Australia
46274,1819729,HONG KONG,Asia>Hong Kong Special Administrative Region>Hong Kong
46274,1643084,INDONESIA,Asia>Republic of Indonesia
46274,1861060,JAPAN,Asia>Japan
46274,1733045,MALAYSIA,Asia>Malaysia
46274,2186224,NEW ZEALAND,Oceania>New Zealand
46274,1694008,PHILIPPINES,Asia>Republic of the Philippines
46274,1880251,SINGAPORE,Asia>Republic of Singapore
46274,1835841,SOUTH KOREA,Asia>Republic of Korea
46274,1668284,TAIWAN,Asia>Taiwan""")
    
    geoLyzard_c5000 = StringIO("""46274,1819730,,Asia>Hong Kong Special Administrative Region,0.0
46274,1609348,,Asia>Kingdom of Thailand>Krung Thep Mahanakhon,0.0
46274,1880251,,Asia>Republic of Singapore,15.0
46274,1835848,,Asia>Republic of Korea>Sŏul-t'ŭkpyŏlsi>Seoul,16.0
46274,6255147,,Asia,0.0
46274,1607530,,Asia>Kingdom of Thailand>Changwat Phra Nakhon Si Ayutthaya,16.0
46274,1668284,,Asia>Taiwan,14.0
46274,1735161,,Asia>Malaysia>Wilayah Persekutuan Kuala Lumpur>Kuala Lumpur,18.0
46274,1643084,,Asia>Republic of Indonesia,0.0
46274,1605651,,Asia>Kingdom of Thailand,0.0
46274,6255151,,Oceania,0.0
46274,1880252,,Asia>Republic of Singapore>Singapore,16.0
46274,1819729,,Asia>Hong Kong Special Administrative Region>Hong Kong,15.0
46274,1835841,,Asia>Republic of Korea,0.0
46274,1701667,,Asia>Republic of the Philippines>City of Manila,17.0
46274,1861060,,Asia>Japan,0.0
46274,1642911,,Asia>Republic of Indonesia>Daerah Khusus Ibukota Jakarta Raya>Jakarta,16.0
46274,1609350,,Asia>Kingdom of Thailand>Krung Thep Mahanakhon>Bangkok,17.0
46274,1850147,,Asia>Japan>Tōkyō-to>Tokyo,16.0
46274,1701668,,Asia>Republic of the Philippines>City of Manila>Manila,18.0
46274,1642907,,Asia>Republic of Indonesia>Daerah Khusus Ibukota Jakarta Raya,0.0
46274,1694008,,Asia>Republic of the Philippines,0.0
46274,1835847,,Asia>Republic of Korea>Sŏul-t'ŭkpyŏlsi,0.0
46274,1733046,,Asia>Malaysia>Wilayah Persekutuan Kuala Lumpur,17.0
46274,1733045,,Asia>Malaysia,0.0
46274,2186224,,Oceania>New Zealand,2.0
46274,1850144,,Asia>Japan>Tōkyō-to,0.0""")

   
    def __init__(self):
        self.ref = CSVResultCollection()
        self.reuters.filename="reuters"
        self.ref.read( self.reuters )
        self.reuters.seek(0)

        self.res = SigCSVResultCollection()
        self.geoLyzard_c5000.filename="geoLyzard_c5000"
        self.res.read( self.geoLyzard_c5000 )
        self.geoLyzard_c5000.seek(0)

    @attr("remote")
    def testMaxMatchDocumentScoringNormalization(self):
        """ verifies that normalizeResultListSize behaves as specified """

        m = MaxMatchDocumentScoring( self.ref,
                                     self.res,
                                     "test" )

        curKey = self.res.data.keys().pop()
        normalized_res = [ g for g in m.normalizeResultListSize( self.res.data[curKey], self.ref.data[curKey] ) ]
        normalized_ref = [ g for g in set(self.ref.data[curKey]) ] 

        # verify that both list or of equal size
        print "xxx", len(normalized_res), "REF", len(normalized_ref)
        assert len(normalized_res) <= len(normalized_ref)

        # verify that only the top (size) entries have been taken!
        print normalized_res
        assert sum(map(itemgetter(0), normalized_res) ) ==  (2*18 + 3*17 + 5*16 )

 
    @attr("remote")
    def testDocumentScoringNormalization(self):
        """ verifies that normalizeResultListSize behaves as specified """

        p = P1DocumentScoring( self.ref,
                               self.res,
                               "test" )

        curKey = self.res.data.keys().pop()
        normalized_res = [ g for g in p.normalizeResultListSize( self.res.data[curKey], self.ref.data[curKey] ) ]

        # verify that both list or of equal size
        assert len(normalized_res) == 1

        # verify that only the top (size) entries have been taken!
        print normalized_res
        assert sum(map(itemgetter(0), normalized_res) ) == 18


        


