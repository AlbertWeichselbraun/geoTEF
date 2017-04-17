#!/usr/bin/env python

"""
   @package dataset.factory
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

from eWRT.util.cache import MemoryBufferCache
from geoTEF.geoTEFconfig import GEO_DB_HANDLE, CACHE_DIR_LOCATION_REF
from geoTEF.dataset.types import SetLocationReference, HierarchyLocationReference

MIN_POP = 10000

class GeoLookup(object):
    """Lookup geo entries """

    def __init__(self):
        self.cache = MemoryBufferCache(CACHE_DIR_LOCATION_REF, cache_file_suffix="."+self.__class__.__name__) 

    def get(self, name):
        """ lookup a GeoEntity 
             @param[in] name an identifier describing the entity.
        """
        return self.cache.fetch( name, self.getGeoLocation )        


    def getGeoLocation(self, identifier):
        """ determins the entities geo-tree based on
             a) the entities name or
             b) the location id in the gazetteer
                (preferred, because no disambiguation is
                 required)
            @param[in] identifier name or gazetteer-id of the location
            @returns a ILocationReference for the given location
        """
        raise NotImplementedError



class LocationReferenceLookup(GeoLookup):
    """ @class LocationReferenceLookup
        creates a SetLocationReference object """

    def _get_in_names_int(self, entity_id):
        """ sets the list of all possibles names for this object based on the
            entitiy_id """
        locationTree = [ entity_id ]
        # determine the location tree
        while True:
            res = GEO_DB_HANDLE.query("select parent_id FROM locatedin WHERE child_id=%s" % locationTree[-1] )
            if not res or res[0]['parent_id'] in locationTree:
                break
            locationTree.append( res[0]['parent_id'] )

        # determine the location's names
        q = "SELECT entity_id, MIN(name) AS name FROM gazetteerentry JOIN hasname ON (gazetteerentry.id = entry_id) WHERE entity_id IN (%s) AND ispreferredname=True AND (lang IN ('en', '')  OR lang IS NULL) GROUP BY entity_id" % (",".join( map(str, locationTree)))
        res = GEO_DB_HANDLE.query( q )
        assert( len(locationTree) == len(res) ) # assert that we do not loose or add any entity(!)
        if not res:
            return []

        idToName = dict( [ (r['entity_id'], r['name']) for r in res ] )
        # print "xxx",idToName
        # print "***",locationTree
        return [ (id, idToName[id]) for id in locationTree ]


    def _get_in_names_str(self, name):
        """ sets a list of all possible names for this object (including superclasses """
        res = GEO_DB_HANDLE.query("select entity_id from gazetteerentry join hasname ON (gazetteerentry.id=entry_id) JOIN gazetteerentity ON (gazetteerentity.id=entity_id) where name ilike '%%%s%%' and population>%s order by population desc limit 1" % (name.replace("'", "\\'"), MIN_POP))
        if not res:
            return []

        entity_id = res[0]['entity_id']
        return self._get_in_names_int( entity_id )


class SetLocationReferenceLookup(LocationReferenceLookup):
    """ @class SetLocationReference
        creates a SetLocationReference object """

    def getGeoLocation(self, identifier):
        """ @returns a SetLocationReference for the given location
        """
        if isinstance(identifier, str):
            locationSet = set( [name for id,name in self._get_in_names_str(identifier)] )
        elif isinstance(identifier, int):
            locationSet = set( [name for id,name in self._get_in_names_int(identifier)] )
        raise "Cannot handle identifier from type ", type(identifier)

        return SetLocationReference( locationSet )
        

class HierarchyLocationReferenceLookup(LocationReferenceLookup):
    """ @class HierarchyLocationReference
        create a HierarchyLocationReference object """

    def getGeoLocation(self, identifier):
        """ @returns a HierarchyLocationReference for the given location 
        """
        if isinstance(identifier,str):
            locationStr = ">".join( [name for id,name in reversed(self._get_in_names_str(identifier)) ] )
        elif isinstance(identifier,int):
            locationStr = ">".join( [name for id,name in reversed(self._get_in_names_int(identifier)) ] )
        else:
            raise "Cannot handle identifier from type ", type(identifier)

        return HierarchyLocationReference( locationStr )
        


if __name__ == '__main__':

   l = HierarchyLocationReferenceLookup()
   g = l.get("europe")
   HierarchyLocationReference.W_HIERARCHY=0.9
   print "g", g

   g2 = l.get("vienna")
   print "g2", g2

   g3 = l.get("perth")
   print "g3", g3

   print "g and g2", g & g2
   print "g2 and g", g2 & g


   print "g3 and g", g3 & g
   print "g and g3", g & g3

   HierarchyLocationReference.W_HIERARCHY=0.0
   print "g2 and g2", g2 & g2
