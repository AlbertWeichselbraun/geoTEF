#!/usr/bin/env python

""" 
 @package output.
 gnuplot.py - Supports the creation of diagrams using gnuplot 
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

__author__  = "Albert Weichselbraun"
__licence__ = "GPL"
__revision__= "$Revision$"

import tempfile
import commands
from os.path import splitext
from libsts.config import GNUPLOT

class GnuPlot(object):
    """ visualizes data files """

    OUTPUT_FORMATS = { '.ps'  : "set terminal postscript\nset output '%s'\n",
                       '.png' : "set terminal png\nset output '%s'\n",
                       '.svg' : "set terminal svg\nset output '%s'\n",
                     }
    _get_ext = lambda self,f: splitext(f)[1]
    

    def __init__( self, fname=None, delimiter="," ):
        (tmp, self.name_gnuplot) = tempfile.mkstemp(".gnuplot", "ctrl")
        self.f=open(self.name_gnuplot, "w")

        self.plots   = []
        # list of plot options
        self.options = []    
        self.x_title = ""
        self.y_title = "" 
        self.delimiter      = delimiter
        self.min_plot_range = {'x': None, 'y': None}
        self.max_plot_range = {'x': None, 'y': None}


    def _get_output_mode(self, fname):
        """ determins the output mode used (display, save as file) """
        if fname is None:
            return ""
        else:
            try:
                return self.OUTPUT_FORMATS[ self._get_ext(fname) ] % fname
            except KeyError:
                raise ValueError, "The extension '%s' is not supported as output format." % self._get_ext(fname) 


    def suggest_max_range(self, dim, v):
        """ suggests the following value as the max plot range of the given dimension to v 
            @param[in] dim   dimension (x,y)
            @param[in] v     value """
        self.max_plot_range[dim] = max( v, self.max_plot_range[dim] )


    def suggest_min_range(self, dim, v):
        """ suggests the following value as min plot range of the given dimension to v 
            @param[in] dim   dimension (x,y)
            @param[in] v     value """
        if self.min_plot_range[dim] is None:
            self.min_plot_range[dim] = v
        else:
            self.min_plot_range[dim] = min( v, self.min_plot_range[dim] )


    def _get_plot_range(self):
        """ @returns a string representing the plot-range of the graph """
        range=""
        for dim in ('x', 'y'):
            if self.min_plot_range[ dim ]!=None and self.max_plot_range[ dim ]!=None:
                range+="[%f:%f]" % ( self.min_plot_range[ dim ], self.max_plot_range[ dim ] )
            else:
                range+="[]"

        return range


    def xy_plot( self, csv_fname, x_col=1, y_col=2, title="Default XY Plot", style="with lines" ):
        """ creates a xy plot of the file """
        if csv_fname.endswith(".gz"):
            csv_fname = "< gzip -dc %s" % csv_fname
        self.plots.append("""'%s' using %d:%d %s title "%s" """ % (csv_fname, x_col, y_col, style, title ) )

    def set_option( self, option, value):
        """ sets the given plot option to the given value
            @param[in] option name of the option to set
            @param[in] value  value of that option"""
        self.options.append( (option,value) )


    def visualize( self, fname=None ):
        """ outputs the plot :) """
        # sets the output mode
        self.f.write( self._get_output_mode( fname ) )
        self.f.write( "\n".join( [ "set %s %s" % (k,v) for k, v in self.options ] )+"\n" )

        self.f.write( "set datafile separator \"%s\"\n" % self.delimiter)
        if self.x_title:
            self.f.write("""set xlabel "%s"\n""" % self.x_title)
        if self.y_title:
            self.f.write("""set ylabel "%s"\n""" % self.y_title)

        # plot the graphs
        self.f.write("plot %s %s\n" % ( self._get_plot_range(), ", ".join(self.plots)) )

        # wait if required
        if fname is None:
            self.f.write("""pause mouse\n""")
        self.f.close()
        print commands.getoutput("%s %s" % (GNUPLOT, self.name_gnuplot) )

    # ---------------------------------------------------------------------------
    # - properties
    # ---------------------------------------------------------------------------


if __name__ == "__main__":
    g=GnuPlot("nocache.csv")
    g.xyPlot("TestPlot")
    g.visualize()

# $Id$
