#!/usr/bin/env python

""" @package output.writer 
    Implements different writer methods for providing .csv output of results."""

import csv
from StringIO import StringIO

class DiagrammOutputWriter(object):
    """ @interface DiagrammOutputWriter
        An interface to classes which provide a string representation (e.g. CSV) of 
        the input data."""

    @staticmethod
    def output(data):
    	"""Returns a string representation of the data.
	   @param[in]  data	A list of (x,y) tuples to write to a CSV file.
	   @return A string containing the data."""
        raise NotImplementedError


class CSVWriter(DiagrammOutputWriter):
    """ @class CSVWriter 
        Outputs the diagramm data in the csv format."""

    @staticmethod
    def output(data):
        """ Returns a csv representation of the diagramm.
	    @param[in]  data	A list of (x,y) tuples to write to a CSV file.
	    @return             A string containing the CSV data. """
        s  = StringIO()
        sw = csv.writer( s, delimiter="\t" )
        sw.writerow( ("x","y") )

        data.sort()

        for tp in data:
            sw.writerow( tp )

        tmp = s.getvalue()
        s.close()
        return tmp

class EchoCSVWriter(DiagrammOutputWriter):
    """ @class CSVWriter 
        Outputs the diagramm data in the csv format."""

    @staticmethod
    def output(data):
        """ Returns a csv representation of the diagramm.
	    @param[in]  data	A list of (x,y) tuples to write to a CSV file.
	    @return             A string containing the CSV data. """
        s  = StringIO()
        sw = csv.writer( s, delimiter="\t" )

        for tp in data:
            sw.writerow( tp )

        tmp = s.getvalue()
        s.close()
        return tmp


class CSVWriterTest(object):

    test_tuples = [ (3,2), (9,1), (1,3), (4,3) ]

    def test_csv_writer(self):
        """ tests the csv writer """
        print CSVWriter.output( self.test_tuples )

     
