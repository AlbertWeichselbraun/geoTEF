#!/usr/bin/env python

"""
   @package scoring.evaluation
"""

# -----------------------------------------------------------------------------------
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

from csv import reader
from eWRT.dataset.factory import HierarchyLocationReferenceLookup
from eWRT.dataset.types import HierarchyLocationReference
try:
    import psyco
    psyco.full()
except ImportError:
    from warnings import warn
    warn("Cannot import psyco!")


class IEvaluationDataSet(object):
    """ @interface IEvaluationDataSet
        An iterator providing two LocationReferences """

    def __iter__(self): return self

    def next(self):
        """ @returns two LocationReference for the evaluation """
        raise NotImplementedError


class EvaluationDataSet(IEvaluationDataSet):
    """ @class EvaluationDataSet
        A class providing an Evaluation dataset """

    def __init__(self, evalDict, goldStandardDict):
        """ initialized the EvaluationDataSet
            @param[in] evalDict a dictionary with the evaluation set's id to LocationReference mappings.
                                Example: {'120033': 'eu.at.Vienna', '120303: 'au.wa.Perth' ,...}
            @param[in] goldStandardDict a dictionary with the gold standard's id to LocationReference mappings.
        """
        try:
            self.evalData = [ ( goldStandardDict[k], evalDict[k] ) for k in evalDict ]
        except KeyError:
            raise "Evaluation and GoldStandard do not comprise the same documents! I cannot evaluate such corpora" 

    def next(self):
        """ @returns two LocationReference for the evaluation """
        try:
            return self.evalData.pop()
        except IndexError:
            raise StopIteration


class FileBasedEvaluationDataSetFactory(object):
    """ @class FileBasedEvaluationDataSetFactory
        abstract class for csv based evaluation datasets """

    def __init__(self, fname):
        self.fname = fname
        self.h     = HierarchyLocationReferenceLookup()

    def get(self):
        """ @returns the dictionary of id's to LocationReference mappings """
        return dict( [ self.getLocationReference(result) for result in reader( open(self.fname) ) ] )

    def getLocationReference(self, result):
        """ reads a data file and returns a list of document_id's and location references.
            @param[in] result a line containing document and the document's tagging result.
            @returns a list of values of type (document_id, ILocationReference)
        """
        raise NotImplementedError


class IdBasedEvaluationDataSetFactory(FileBasedEvaluationDataSetFactory):
    """ @class IdBasedEvaluationDataSetFactory
        creates an EvaluationDataSet based on csv files containing document- and gazetteer-id.
         document_id,gazetteer_id,... """

    def getLocationReference(self, result):
        try:
            doc_id, gaz_id = result[0], int(result[1])
            return (doc_id, self.h.get( gaz_id ) )
        except IndexError:
            return (result[0], HierarchyLocationReference(""))


class ReutersEvaluationDataSetFactory(FileBasedEvaluationDataSetFactory):  
    """ @class ReutersEvaluationDataSetFactory
        creates an (Goldstandard) EvaluationDataSet based on the reuters database
        geo annotations """

    def getLocationReference(self, result):
        try:
            doc_id, gaz_id = result[0], result[1]
            return (doc_id, self.h.get( gaz_id ) )
        except IndexError:
            return (result[0], HierarchyLocationReference(""))


   
class Evaluation(object):
    """ @class Evaluation
        computes the utility score for the given settings """

    @staticmethod
    def computeScore( evalSet ):
        """ computes the utility score for the given evaluation
            set """
        score = sum( [gold & tagged for gold, tagged in evalSet] )
        return score
        


if __name__ == '__main__':
    pass

# $Id$

