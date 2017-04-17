#!/usr/bin/env python

""" install geoTEFF :) """

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
      ###########################################
      ## Metadata
      name="geoTEF",
      version      = "0.02",
      description  = 'eWRT',
      author       = 'Albert Weichselbraun',
      author_email = 'albert.weichselbraun@wu.ac.at',
      url          = 'http://www.semanticlab.net/index.php/Geo_Tagger_Evaluation_Framework',
      license      = "GPL3", 
      package_dir  = {'': 'src'},

      ###########################################
      ## Scripts
      # scripts = ['src/input/corpus/reuters/reuters.py' ],
 
      ###########################################
      ## Package List
      packages     = ['geoTEF',
                      'geoTEF.data',
                      'geoTEF.data.plot',
                      'geoTEF.data.results',
                      'geoTEF.dataset',
                      'geoTEF.dataset.ipm',
                      'geoTEF.dataset.onto',
                      'geoTEF.dataset.onto.terminology',
                      'geoTEF.dataset.onto.relationtypes',
                      'geoTEF.input',
                      'geoTEF.output',
                      'geoTEF.output.gnuplot',
                      'geoTEF.output.writer',
                      'geoTEF.scoring',
                      'geoTEF.tagger',
                     ],

      ###########################################
      ## Package Data
)
