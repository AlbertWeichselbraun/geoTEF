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
from eWRT.ontology.compare.relationtypes import RelationTypes

class RelationTypeReference(ILocationReference):
    """ Superclass for all Terminology comparison operations """
    def __init__(self, e):
        ILocationReference.__init__(self)
        self.e = e 

    def __and__(self, o):
        raise NotImplemented

    def __or__(self, o):
        raise NotImplemented


class EqualRel(RelationTypeReference):
    """ compares whether the terms are equal or not """

    def __or__(self, o):
        assert isinstance(o, RelationTypeReference)
        return self.e == o.e and 1. or 0.

class GroupRel(RelationTypeReference):
    """ compares the terms based on verbs, prepositions, etc. """

    rt = RelationTypes()

    def __init__(self, e):
        RelationTypeReference.__init__(self, e)
        self.p  = self.rt.partitionRelation( e )  # contains the partitioned relation

class EqualGroup(GroupRel):
    """ compares the terms based on verbs, prepositions, etc. """

    def __or__(self, o):
        return 1.0 if self.p == o.p else 0.

class SimilarGroup(GroupRel):
    """ compares the terms based on verbs, prepositions, etc. using 
        heuristics to evaluate the results """

    @staticmethod 
    def getOverlap(p1, p2, key='v'):
        """ returns the percentage of overlapping items between p1 and p2
            @param[in] p1  list of items
            @param[in] p2  list of items
            @returns percentage of overlap between p1 and p2
        """
        if not key in p1 or not key in p2:
            return 0.

        intersection = set(p1[key]).intersection( set(p2[key]) )
        maxLen       = max(len(p1[key]), len(p2[key]))
        return len( intersection ) / float( maxLen )

    def __or__(self, o):
        if self.e == o.e or (self.p and self.p == o.p):
            return 1.0

        vScore = self.getOverlap( self.p, o.p, 'v' )
        if vScore == 0.:
            return 0.
        else:
            pScore = self.getOverlap( self.p, o.p, 'p' )
            return 0.75*vScore + 0.25 * pScore




# --------------------------------------------------------------------------------
# 
# UNITTESTING
#   
# --------------------------------------------------------------------------------

class TestRelationTypeReference(object):

    def testEqualRel(self):
        assert EqualRel("focus in") | EqualRel("focus in") == 1.
        assert EqualRel("focus in") | EqualRel("focus") == 0.

    def testEqualGroup(self):
        assert EqualGroup("focus in") | EqualGroup("focus in") == 1.
        assert EqualGroup("focus in") | EqualGroup("focus") == 0.
        assert EqualGroup("may focus in") | EqualGroup("focus in") == 1.
        assert EqualGroup("may focus on") | EqualGroup("has been focusing on") == 1.

        assert EqualGroup("e.g.") | EqualGroup("????") == 0.

    def testSimilarGroupOverlap(self):
        assert SimilarGroup.getOverlap({'v': (1,2,3,4)}, {'v': (2,3,4,9,10)}) == 0.6
        assert SimilarGroup.getOverlap({'v': (1,)}, {'v': (2,3,4,9,10)}) == 0. 

        assert SimilarGroup.getOverlap( {}, {'v': (2,3,4)} ) == 0.
        assert SimilarGroup.getOverlap( {}, {} ) == 0.

    def testSimilarGroup(self):
        assert SimilarGroup("may focus on") | SimilarGroup("has been focusing on") == 1.
        assert SimilarGroup("may focus in") | SimilarGroup("has been focusing on") == .75
        assert SimilarGroup("on") | SimilarGroup("has been focusing on") == .0
        print SimilarGroup("jumps on") | SimilarGroup("has been running and jumping to")
        assert SimilarGroup("jumps on") | SimilarGroup("has been running and jumping to") == .375

        print SimilarGroup("e.g.") | SimilarGroup("e.g.")
        assert SimilarGroup("e.g.") | SimilarGroup("e.g.") == 1.
        assert SimilarGroup("e.g.") | SimilarGroup("????") == 0.
        assert SimilarGroup("to") | SimilarGroup("in") == 0.
        assert SimilarGroup("to") | SimilarGroup("to") == 1.





    
    
