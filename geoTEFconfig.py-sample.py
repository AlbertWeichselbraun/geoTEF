#!/usr/bin/env python

""" config - contains all important file locations """

__Revision__="$Id$"

import os.path
from warnings import warn

# geotagger database connection
try:
    from eWRT.access.db import PostgresqlDb
    DBNAME = ""
    DBHOST =""
    DBUSER =""
    DBPASS =""
    GEO_DB_HANDLE = PostgresqlDb(DBNAME, DBHOST, DBUSER, DBPASS)
except ImportError:
    warn("Warning: Cannot import postgresql modules")

CACHE_DIR_LOCATION_REF= os.path.join( os.path.dirname(__file__), "cache", "LocationReference" )
REUTERS_GOLDSTD_REF   = os.path.join( os.path.dirname(__file__), "data", "goldstd_reuters.csv" )

# $Id$

