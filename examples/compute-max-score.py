#!/usr/bin/env python

""" this script computes the maximum possible score based on the reuters coprus """

from csv import reader
from gzip import open

FNAME = "corpora/reuters.csv.gz"

d = dict( [ (document_id, geo_entity_id) for document_id, geo_entity_id, geo_name, geo_url in reader( open( FNAME ), delimiter="," ) if geo_entity_id ] )

print "Number of documents with at least one attached geographic location: %d" % len(d)
