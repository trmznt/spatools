
import sys, os
from spatools.lib.utils import cout, cerr
from spatools.lib.sqlmodels.handler_interface import base_sqlhandler
from spatools.lib.sqlmodels import schema

from pandas import DataFrame


class SQLHandler(base_sqlhandler):

    Batch = schema.Batch
    Sample = schema.Sample
    Variant = schema.Variant
    Genotype = schema.Genotype


    def __init__(self, dbfile, initial=False):
        cerr("Opening db: %s" % dbfile)
        if not initial and not os.path.isfile(dbfile):
            cerr('ERR - sqlite db file not found: %s' % dbfile)
            sys.exit(1)
        if initial and os.path.isfile(dbfile):
            cerr('ERR - sqlite db file already exists: %s' % dbfile)
            sys.exit(1)
        self.dbfile = dbfile
        self.engine, self.session = schema.engine_from_file(dbfile)


    def initdb(self, create_table = True):
        if create_table:
            schema.Base.metadata.create_all(self.engine)
        from fatools.lib.sqlmodels.setup import setup
        setup( self.session )
        cout('Database at %s has been initialized.' % self.dbfile)


