#!/usr/bin/env python

"""
   @package geoTEF.dataset.types
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
__revision__ = "$Revision$"

from math import pow


class ILocationReference(object):
    """ @interface ILocationReference
        A reference describing a geographic location. It is necessary that the distance between arbitrary 
        two GeoReferences is computable. 
        
        Examples: eu>at>Vienna, oz>au>Perth>Claremont; 12.35 lat/13.48 long, 33.21 lat/ 32.12 long. 

        The ILocationReference decides how related two instances of the class are using an overwriten __and__() method. 
        @code distance = loc1 & loc2 @endcode
    """

    def __and__(self, refObj):
        """ @returns a number representing the difference between this
                     object and a reference object. """
                     

class SetLocationReference(ILocationReference):
    """ @class SetLocationReference
        compares locations based on whether the same entities
        occure. """

    def __init__(self, locationRefSet):
       """ @param[in] locationRefSet a set containing the location tree """
       assert(isinstance(locationRefSet, set))
       self.locationRefSet = locationRefSet

    def __contains__(self, o):
        """ tests whether both elements are equal """
        return self.locationRefSet.issubset( o.locationRefSet )

    def __and__(self,o):
        """ @returns one if self is contained in o otherwise zero """
        if self in o: return 1.
        else: return 0.

    def __str__(self):
        return "<SetLocationReference (%s)>" % (", ".join(self.locationRefSet) )


class HierarchyLocationReference(ILocationReference):
    """ @class HierarchyLocationReference
        displays and computes location based on a hierarchical
        representation.

        e.g. "eu>at>Vienna", "oz>au>wa>Perth"
    """
    SEPARATOR    = ">"
    W_SUBCLASS   = 1.0  # defines by which factor every further hierarchy is penalized
    W_SUPERCLASS = 0.0

    def __init__(self, locationString):
        """ @param[in] locationString a string representing the given location """
        self.locationString = locationString


    def __contains__(self, o):
        """ determins whether the location of self is contained in o """
        return self.getNumberOfHierarchyLevels >=0 


    def __and__(self, o):
        """ Compares the current object ('self') with 'o'.
            @param[in] o comparison object
            @returns a number between 0 and 1 indicating the relationsship between 'self' and 'o'.
               0 ... the objects are not related
               1 ... the objects are identical
        """
        h = self.getNumberOfHierarchyLevels(o)
        if h == -1:
            h_super = HierarchyLocationReference.getNumberOfHierarchyLevels(o, self)
            if h_super == -1: return 0.
            else            : return pow(HierarchyLocationReference.W_SUPERCLASS, h_super )
        elif h == 0:
            return 1.
        else:
            return pow(HierarchyLocationReference.W_SUBCLASS, h) 

                     
    def getNumberOfHierarchyLevels(self, o):
        """ determins how much hierarchy levels o is more detailed
            than self.

            @param[in] o the comparison object
            @returns a number indicating the number of hierarchy levels.
                       0  ... both objects represent the same location
                       -1 ... both objects represent different locations which are not contained in each other
                       n ...  self represents a more detailed location with n levels of additional detail.
        """
        try:
            prefix, suffix = o.locationString.split( self.locationString )
            if prefix:
                return -1
            else:
                return len( suffix.split( HierarchyLocationReference.SEPARATOR ) )-1
        except ValueError:
            return -1


    def __str__(self):
        return "<HierarchyLocationReference (%s)>" % (self.locationString)



if __name__ == '__main__':
    from unittest import TestCase, main

    class TestHierchyLocationReference(TestCase):
        l1 = HierarchyLocationReference("Europe>Republic of Austria>Bundesland Wien")
        l2 = HierarchyLocationReference("Europe")
        l3 = HierarchyLocationReference("Oceania>Commonwealth of Australia>State of Western Australia>Perth")
        

        
        def testAnd(self):
            HierarchyLocationReference.W_SUBCLASS   = 0.8
            HierarchyLocationReference.W_SUPERCLASS = 0.5

            self.assertAlmostEqual( self.l2 & self.l1, pow(0.8,2) )
            self.assertAlmostEqual( self.l1 & self.l2, pow(0.5,2) )
            self.assertAlmostEqual( self.l3 & self.l1, 0.0 )
            self.assertAlmostEqual( self.l1 & self.l3, 0.0 )

    main()
