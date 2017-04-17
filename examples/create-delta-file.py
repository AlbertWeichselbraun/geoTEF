#!/usr/bin/env python

import os.path
from eWRT.access.db import PostgresqlDb
from eWRT.util.cache import DiskCached
from geoTEF.input import CSVResultCollection, SigCSVResultCollection
from csv import reader, writer
from glob import glob
from operator import itemgetter
from gzip import GzipFile

DELTA_DIR = "./delta" 
TOP_EVAL_IDS = 25
GEO_EVAL_DB = PostgresqlDb("geoEval", "xmdimrill.ai.wu.ac.at", "geoEval", "x12o21c")

@DiskCached(".get_corpora-Cache")
def get_corpus(corpusUrl):
    """ retrieves the given corpus using the reader
        specified in the corpusUrl

        @param[in] corpusUrl e.g. CSVResultCollection:/home/..../reuters.csv
        @returns the corpus as dictionary
    """
    assert ":" in corpusUrl
    readerClass, path = corpusUrl.split(":",1)

    reader = eval(readerClass)()
    if path.endswith(".gz"):
        reader.read( GzipFile(path) )
    else:
        reader.read( open(path) )

    return reader


def determine_evaluation_ids( ):
    evaluation_ids = []
    for fname in glob(  os.path.join( DELTA_DIR, "*.csv" ) ):
        content = [ map(float,d) for d in reader( open(fname) ) ]
        
        for idx in xrange(1,4):
            content.sort( key=itemgetter(idx), reverse=False)
            evaluation_ids.extend( [ int(c[0]) for c in content[:TOP_EVAL_IDS]] )

    return evaluation_ids


def unique(l):
    """ returns the unique list """
    i = 0
    while i < len(l):
        try:
            del l[l.index(l[i], i + 1)]
        except:
            i += 1 

    return l


def get_geo_urls(id):
    # do not allow more geo entities as specified in the gold standard set(!)
    id = str(id)
    res = [ unique( [ t[1].entityDict['geoUrl'] for t in sorted(tagger_res.data[id], reverse=True)])  for tagger_res in TAGGER_RESULTS ] 
    reference_len = len(res[3])

    # return [ '\n'.join([ r for r in rr[:reference_len] ]) for rr in res ]
    return [ '\n'.join([ r for r in rr[:7] ]) for rr in res ]


def get_article( id ):
    """ returns the text of the given article from the database """
    res = GEO_EVAL_DB.query("SELECT id, headline, content FROM jgis.reuters WHERE id=%s" % id )
    return "%s (%d)\n%s" % ( res[0]['headline'], res[0]['id'], res[0]['content'] )



TAGGER_RESULTS = (get_corpus( 'CSVResultCollection:/home/albert/ipm-geoeval/corpora/Alchemy.csv.gz' ),
                  get_corpus('SigCSVResultCollection:/home/albert/ipm-geoeval/corpora/geoLyzard_Default_C500000.csv.gz'),
                  get_corpus('SigCSVResultCollection:/home/albert/ipm-geoeval/corpora/geoLyzard_Amitay_C500000.csv.gz'),
                  get_corpus('CSVResultCollection:/home/albert/ipm-geoeval/corpora/reuters.csv.gz'),
               )

ff=open("./delta/final_evaluation.csv", "w")
wf=writer(ff)
d=determine_evaluation_ids()
print len(d), len( set(d) )
evaluation_ids = set( determine_evaluation_ids() )

for eId in evaluation_ids:
    content  = get_article( eId )
    geo_urls = get_geo_urls( eId )

    if geo_urls != None:
        wf.writerow( [content] + geo_urls )
        ff.flush()

ff.close()



        

