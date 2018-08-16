
from spatools.lib.utils import cout, cerr, cexit
from spatools.lib import const
from spatools.lib import dictfmt

import attr
import time

# SNP

class LocusMixIn(object):
	pass

class GenotypeMixIn(object):

    @staticmethod
    def csv2dict( *args, **kwargs ):
        return dictfmt.genotype_csv2dict( *args, **kwargs )

class PanelMixIn(object):
    pass


# Sample


class SampleMixIn(object):

    def _update(self, obj):

        if type(obj) == dict:
            if 'code' in obj:
                self.code = obj['code']
            if 'type' in obj:
                self.type = obj['type']
            if 'altcode' in obj:
                self.altcode = obj['altcode']
            if 'category' in obj:
                self.category = obj['category']
            if 'remark' in obj:
                self.remark = obj['remark']

        else:

            raise NotImplementedError('PROG/ERR - not implemented yet')


    def add_genotypes(self, assay_dicts):
        pass




class BatchMixIn(object):
    
    def add_samples(self, sample_dicts):
        pass

    def add_genotypes(self, genotype_dicts):
        pass


# Auxiliary mixin, probably should be in separate file when fully implemented

class NoteMixIn(object):

    pass

class BatchNoteMixIn(object):

    pass

class SampleNoteMixIn(object):

    pass

class MarkerNoteMixIn(object):

    pass

class PanelNoteMixIn(object):

    pass

class FSANoteMixIn(object):

    pass

class ChannelNoteMixIn(object):

    pass

class AlleleSetNoteMixIn(object):

    pass
