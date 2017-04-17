#!/usr/bin/env python
"""
   @package dataset.types.ipm
   datatypes used for the evaluations in the ipm paper
"""

# -----------------------------------------------------------------------------------
# geoTEF - geo Tagger Evaluation Framework
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
__revision__ = "$Revision: 389 $"

from eWRT.ws.geonames import GeoEntity, GeoNames
from eWRT.config import GEO_ENTITY_SEPARATOR
from geoTEF.dataset.types import ILocationReference
from operator import mul
from nose.plugins.attrib import attr
import math

VALID_NEIGHBOR_LEVLES = (2, 3,) # country, state

class ILR(ILocationReference):
    """ LR - Basis LocationReference Interface for these evaluations """

    def __init__(self, g):
        assert isinstance(g, GeoEntity)
        self.g = g

    def __and__(self,o):
        raise NotImplemented

    def __or__(self, o):
        """ returns a skalar value indicating the strength
            of the relationship between the two GeoEntities """
        raise NotImplemented

    def __hash__(self):
        return self.g.__hash__()

    def __cmp__(self, r):
        return self.g.__cmp__(r.g)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "<%s geonames_id=%s>" % (self.__class__.__name__, self.g['id'])

class EqualLR(ILR):
    """ verifies whether the locations are exactly the same """

    def __and__(self, o):
        assert isinstance(o, ILR)
        return self.g == o.g and 1 or 0

    def __or__(self, o):
        return float( self.__and__(o) )

class CILR(ILR):
    """ Abstract class used for Contain(s|ed) relations """

    def getUtility(self, lessDetailed, moreDetailed, userPrefs):
        """ returns the utility factor based on the user preferences """
        assert isinstance(lessDetailed, GeoEntity) | isinstance(moreDetailed, GeoEntity)

        if lessDetailed == moreDetailed:
            return 1.0

        s = len( lessDetailed.entityDict['geoUrl'].split(GEO_ENTITY_SEPARATOR) )-1
        o = len( moreDetailed.entityDict['geoUrl'].split(GEO_ENTITY_SEPARATOR) )-1
        relevant_factors = userPrefs[s:o]
        return reduce( mul, relevant_factors )


class ContainsLR(CILR):
    """ Checks whether the comparison GeoEntity containes the reference """

    userPrefs = [ 0.5, 0.6, 0.8, 0.9, 0.99 ]

    def __and__(self, o):
        assert isinstance(o, ILR)
        return self.g.contains(o.g) and 1 or 0

    def __or__(self, o, userPrefs=None):
        if not userPrefs:
            userPrefs = self.userPrefs
        if self.__and__(o):
            return self.getUtility( self.g, o.g, userPrefs )
        else:
            return 0.0

class ContainedLR(CILR):
    """ Checks whether the comparison GeoEntity is contained in the reference """

    userPrefs = [0.1, 0.8, 0.9, 0.9, 0.99]

    def __and__(self, o):
        assert isinstance(o.g, GeoEntity)
        return o.g.contains(self.g) and 1 or 0

    def __or__(self, o, userPrefs=None):
        if not userPrefs:
            userPrefs = self.userPrefs
        if self.__and__(o):
            return self.getUtility( o.g, self.g, userPrefs )
        else: 
            return 0.0

class ContainsOrContainedLR(CILR):
    """ Checks whether the GeoEntity contains or is contained by the
        reference """
    def __and__(self, o):
        assert isinstance(o.g, GeoEntity)
        return (self.g.contains(o.g) or o.g.contains(self.g)) and 1 or 0

    def __or__(self, o):
        if self.g.contains(o.g):
            return ContainsLR( self.g ) | ContainsLR( o.g )
        elif o.g.contains(self.g):
            return ContainedLR( self.g) | ContainedLR( o.g )
        else:
            return 0.0


class NeighborLR(ILR):
    """ Checks whether the two references are direct neighbors """

    userPrefs = [ 0.0, 0.3, 0.6, 1.0 ] # utility weight per neighbor level (continent, country, state, city)

    def __and__(self, o):
        if self.g == o.g:
            return 1
        if self.g['level'] != o.g['level'] or self.g['level'] not in VALID_NEIGHBOR_LEVLES:
            return 0 

        #neighbor_ids = [ g.id for g in  GeoNames.getNeighbors(self.g) ]
        return (o.g in GeoNames.getNeighbors(self.g)) and 1 or 0

    def __or__(self, o, userPrefs = None):
        if self.g == o.g:
            return 1.0
        if not userPrefs:
            userPrefs = self.userPrefs
        if not self.__and__(o):
            return 0.0
        else:
            return userPrefs[ self.g['level']-1 ]



class ALR(ILR):
    """ Checks whether two references can be related if we use the A-measure 
        (that's the case if both of them are in the same country)
    """

    def __and__(self, o):
        """ check whether both entities are in the same country """
        return (self.g.highestCommonLevel(o.g)>=2) and 1 or 0

    def __or__(self, o):
        if not self.__and__(o):
            return 0.0
        else:
            # print self.g.entityDict['geoUrl'], self.g.getCountry().entityDict['area']
            area = self.g.getCountry().entityDict['area']
            expected_distance = math.sqrt(area/math.pi) / 3
            real_distance     = self.points2distance( (self.g['latitude'],self.g['longitude']), 
                                                      (o.g['latitude'],o.g['longitude']) )
            
            f_eval = max(0, (1-real_distance/expected_distance))
            uh_c = float(self.g.highestCommonLevel(o.g))/float(max(self.g['level'], o.g['level']))
            return uh_c + (1-uh_c) * f_eval

    @staticmethod
    def points2distance(x,  y):
        """
        Calculate distance (in kilometers) between two points given as (latt, long) pairs
        based on Haversine formula (http://en.wikipedia.org/wiki/Haversine_formula).
        Implementation inspired by JavaScript implementation from 
        http://www.movable-type.co.uk/scripts/latlong.html

        @param[in] x  first point (latt, long)
        @param[in] y  second point (latt, long)
        """
        start_long = math.radians(x[1])
        start_latt = math.radians(x[0])
        end_long = math.radians(y[1])
        end_latt = math.radians(y[0])
        d_latt = end_latt - start_latt
        d_long = end_long - start_long
        a = math.sin(d_latt/2)**2 + math.cos(start_latt) * math.cos(end_latt) * math.sin(d_long/2)**2
        c = 2 * math.atan2(math.sqrt(a),  math.sqrt(1-a))
        return 6371 * c



class OntologyLR(ILR):
    """ Checks whether two references are related if we combine contains/neighbor relations
    """
    userPrefs = [ 0.0, 0.3, 0.6, 1.0 ] # utility weight per neighbor level (continent, country, state, city)

    def __and__(self, o):
        return max( ContainsOrContainedLR(self.g) & ContainsOrContainedLR(o.g), self._checkNeighbor(o.g) )
        
    def _checkNeighbor(self, o):
        """ checks whether it is possible to construct a neighbor relation between
            the given two entities 
            => check, whether the entities are level-2-neighbors on a state level
            => check, whether the entities are level-2-neighbors on a country level
        """
        # check state level
        if self.g['level']>=3 and o['level']>=3:
            if self.twoLevelCheckNeighbor( self.g.getState(), o.getState() ) == 1:
                return 1

        # check country level
        if self.g['level']>=2 and o['level']>=2:
            return self.twoLevelCheckNeighbor( self.g.getCountry(), o.getCountry() )

    @staticmethod
    def twoLevelCheckNeighbor(s, o):
        """ checks whether the two given entries are at least
            two level neighbors
            @param[in] s ... first geo entity
            @param[in] o ... second geo entity
        """
        # verify whether both entries are at the same level and 
        # on a state or country level 
        assert s['level'] == o['level'] and s['level'] >=2 and s['level'] <= 3

        s_neighbor_ids = [ g.id for g in  GeoNames.getNeighbors(s) ]
        o_neighbor_ids = [ g.id for g in  GeoNames.getNeighbors(o) ]

        if o.id in s_neighbor_ids or len( set(s_neighbor_ids).intersection(o_neighbor_ids) ) != 0:
            return 1
        else:
            return 0

    def __or__(self, o):
        ## check the various ontological dimensions

        # equal
        if self.g == o.g:
            return 1.0

        # hierarchy
        elif ContainsOrContainedLR(self.g) & ContainsOrContainedLR(o.g):
            return ContainsOrContainedLR(self.g) | ContainsOrContainedLR(o.g)

        # level 1 neighbor => return
        elif NeighborLR(self.g) & NeighborLR(o.g):
            return NeighborLR(self.g) | NeighborLR(o.g)

        # potential state level (3) neighbor
        elif self.g['level']>=3 and o.g['level']>=3 and self.twoLevelCheckNeighbor( self.g.getState(), o.g.getState() ):
            return self.userPrefs[2] * (ContainsOrContainedLR( self.g.getState()) | ContainsOrContainedLR( self.g ))
                

        # potential country level (2) neighbor
        if self.g['level']>=2 and o.g['level']>=2 and self.twoLevelCheckNeighbor( self.g.getCountry(), o.g.getCountry() ):
            return self.userPrefs[1] * (ContainsOrContainedLR( self.g.getCountry()) | ContainsOrContainedLR( self.g ))
         
        return 0.0


            
       
class TestILR(object):

    def __init__(self):
        g = lambda x: GeoEntity.factory( id=x )[0]
        self.EXAMPLE_ENTITIES = { '.ch'       : g(2658434 ),
                                  '.at'       : g(2782113 ),
                                  '.carinthia': g(2774686 ),
                                  '.styria'   : g(2764581 ),
                                  '.eu'       : g(6255148 ),
                                  'villach'   : g(2762372 ),
                                  'hermagor'  : g(2776497 ),
                       }

        # problematic usecases to investigate (!)
        self.p1 = ( g(2077456), # .au
                    g(1814991), # .ch
                    g(3017382), # .fr
                    g(2921044), # .de
                    g(3175395), # .it
                    g(1861060), # .jp
                    g(2750405), # .nl
                    g(953987),  # .sa
                    g(2658434), # .ch
                    g(2635167), # uk
             )
        self.p2 = ( g(6252001), # .us
                    g(2643743), # .uk/London
                    g(4292188), # .us/Kentucky/Frankfurt
                    g(2988507), # .fr/Paris
                    g(3167896), # .it/San Paolo
                    g(2759793), # .nl/Amsterdam
                    g(1819727), # .hk (Hong Kong)
                    g(6354908), # .ca/Nova Scotia/Sydney
                    g(993800),  # .sa/Johannesburg
                  )

    @attr("remote")
    def testContainsLR(self):
        """
                w0   w1          w2  
              eu > at > Carinthia > Villach
              eu > at
        """
        e = dict( [ (key,ContainsLR(g)) for key,g in self.EXAMPLE_ENTITIES.items()  ] )

        assert (e['.at'] | e['.eu']) == 0.
        assert (e['.eu'] | e['.at']) == ContainsLR.userPrefs[0]
        assert (e['.carinthia'] | e['villach'] ) == ContainsLR.userPrefs[2]
        assert (e['.at']        | e['villach'] ) == ContainsLR.userPrefs[2] * ContainsLR.userPrefs[1]

        assert e['.eu'] & e['.at']
        assert not e['.at'] & e['.eu']

        # equal
        assert e['.at'] | e['.at'] == 1.0

    @attr("remote")
    def testContainsOrContainedLR(self):
        cse = dict( [ (key,ContainsLR(g)) for key,g in self.EXAMPLE_ENTITIES.items()  ] )
        cso = dict( [ (key,ContainsOrContainedLR(g)) for key,g in self.EXAMPLE_ENTITIES.items()  ] )

        assert cse['.eu'] | cse['.at'] == cso['.eu'] | cso['.at']
        assert cse['.at'] | cse['.eu'] < cso['.eu'] | cso['.at']

        # equal
        assert cse['.at'] | cse['.at'] == 1.0
      
    @attr("remote")
    def testContainedLR(self):
        csd = dict( [ (key,ContainedLR(g)) for key,g in self.EXAMPLE_ENTITIES.items()  ] )
        assert csd['villach'] | csd['.eu'] == ContainedLR.userPrefs[0] * ContainedLR.userPrefs[1]  * ContainedLR.userPrefs[2]
        # equal
        assert csd['villach'] | csd['villach'] == 1.0

    @attr("remote")
    def testNeighbor(self):
        e = dict( [ (key,NeighborLR(g)) for key,g in self.EXAMPLE_ENTITIES.items()  ] )
        assert e['.at'] & e['.at']
        assert e['.at'] | e['.at'] == 1.
        assert e['.at'] & e['.ch'] 
        assert e['.at'] | e['.ch'] == NeighborLR.userPrefs[1]

        assert e['.carinthia'] & e['.styria'] 
        assert e['.carinthia'] | e['.styria']  == NeighborLR.userPrefs[2]

    @attr("remote")
    def testALR(self):
        e = dict( [ (key,ALR(g)) for key,g in self.EXAMPLE_ENTITIES.items()  ] )
        assert e['villach'] | e['hermagor'] > e['.carinthia'] | e['.styria']
        assert e['.carinthia'] | e['hermagor'] > e['.styria'] | e['hermagor']

        assert e['villach'] | e['villach'] == 1.0
        assert e['.at'] | e['.ch'] == 0.0

    @attr("remote")
    def testDistance(self):
        """ verifies the results based on test data taken from:
             http://www.movable-type.co.uk/scripts/latlong.html
        """
        lainach = (46.853559,12.930007)
        rangersdorf = (46.863067,12.964211)
        assert 2.8 <= ALR.points2distance(lainach, rangersdorf) <= 3.2

        wien = (48.229247,16.375122)
        linz = (48.310373,14.287033) # distanz ~ 154.8 km
        assert 154 <=ALR.points2distance(wien, linz) <= 155

    @attr("remote")
    def testOntologyLR(self):
        e = dict( [ (key,OntologyLR(g)) for key,g in self.EXAMPLE_ENTITIES.items()  ] )
        assert e['villach'] & e['hermagor']
        assert e['villach'] & e['.ch']
        assert e['villach'] & e['.eu']

        # values
        print "testOLR1 (at,ch)", e['.at'] | e['.ch']
        print "TestOLR2", e['villach'] | e['.ch']

        assert e['.at'] | e['.ch'] == OntologyLR.userPrefs[1]
        assert e['.at'] | e['.ch'] > e['villach'] | e['.ch']

        # equal = 1.0
        assert e['.at'] | e['.at'] == 1.0

    @attr("remote")
    def testEqualLR(self):
         e = dict( [ (key,EqualLR(g)) for key,g in self.EXAMPLE_ENTITIES.items()  ] )
         for name, entity in e.iteritems():
            if name != 'villach':
                assert e['villach'] & entity == 0
                assert e['villach'] | entity == 0.
            else:
                assert e['villach'] & entity == 1
                assert e['villach'] | entity == 1.0

     



# ======================================================================== 
#
#  U N I T T E S T S
#
# ======================================================================== 


if __name__ == '__main__':
    c = TestILR()
    c.testOntologyLR()
    c.testALR()
    c.testDistance()
    c.testContainsLR()
    c.testContainsOrContainedLR()
    c.testContainedLR()
    c.testNeighbor()
