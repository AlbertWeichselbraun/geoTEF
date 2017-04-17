#!/usr/bin/env python

""" @package output
    Classes for recording and outputting simulation data.
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

import writer
import unittest
import sys
from operator import itemgetter

__author__  = "Albert Weichselbraun"
__licence__ = "GPL"
__revision__= "$Revision$"

class Diagram(object):
    """ @class Diagram
        Saves simulation results. 
	Simulation data is added using the @link add_data_point function."""

    def __init__(self):
        """ Initialize the datapoint store """
        self.data = []

    def add_data_point(self, point):
        """ Adds a data point (represented as a tuple) to the diagram.
	    @param[in] point A tuple (x, y) containing the new data point."""
        assert( isinstance(point, tuple) )
        self.data.append( point )

    def output(self, dow):
        """ Outputs a diagram using a @link output.writer.DiagrammOutputWriter(). 
	    @param[in] dow A DiagrammOutputWriter used to format the diagram data."""
        assert( isinstance(dow, writer.DiagrammOutputWriter) )
        return dow.output( self.data )

    def get_max_value(self, column):
        """ returns the maximum of the given column """ 
        return max( map(itemgetter(column), self.data) )


class DiagramTest( object ):

    DATA_POINTS = [ (7,2), (1,3), (9,3), (4,22) ]
    DATA_POINTS_MAX = 9

    def setUp(self):
        """ create test diagramm instance """
        self.d=Diagram()
        map( self.d.add_data_point, self.DATA_POINTS)

    def testDiagram(self):
        """ tests the diagramm test """
        print self.d.output( writer.CSVWriter() )

    def testXMax(self):
        """ tests whether the diagramm correctly identifies x_max """
        self.assertEqual(self.d.get_max_value(column=0), self.DATA_POINTS_MAX)


# $Id: __init__.py 359 2009-01-09 14:07:00Z albert $
