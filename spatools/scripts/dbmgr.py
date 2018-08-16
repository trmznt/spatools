
from spatools.lib import dbmgr
from spatools.lib.utils import cerr

def init_argparser( parser=None ):
	return dbmgr.init_argparser( parser )


def main(args):

	dbmgr.main( args )