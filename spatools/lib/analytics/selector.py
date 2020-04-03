
from itertools import cycle
from spatools.lib.analytics.sampleset import SampleSet, SampleSetContainer
from spatools.lib.const import peaktype

colour_scheme = {

    # 12 categorical colours from ColorBrewer2
    'cb2':    [ '#1f78b4','#33a02c','#e31a1c','#ff7f00','#6a3d9a','#b15928',
                '#a6cee3','#b2df8a','#fb9a99','#fdbf6f','#cab2d6','#ffff99'],

    # 15 continuous colours from ggplot2

    'ggplot2':[ '#00ba39', '#00b0f6', '#fd61d1', '#c99800', '#00bf7d', '#619cff',
                '#ff67a4', '#a3a500', '#00c0af', '#b983ff', '#f8766d', '#6bb100',
                '#00bcd8', '#e76bf3', '#e58700' ],

    # 20 categorical colours from Vega
    'vega20': [ "#1f77b4", "#aec7e8", "#ff7f0e", "#ffbb78", "#2ca02c", "#98df8a",
                "#d62728", "#ff9896", "#9467bd", "#c5b0d5", "#8c564b", "#c49c94",
                "#e377c2", "#f7b6d2", "#7f7f7f", "#c7c7c7", "#bcbd22", "#dbdb8d",
                "#17becf", "#9edae5" ],

    # 20 categorial colours from IWantHue
    'hue20':  [ "#7ebbc7", "#6d38c0", "#72dc59", "#cc4dc4", "#cfd94a", "#6f68c9",
                "#649a40", "#c2477b", "#68d5a9", "#cd3f41", "#637dac", "#dc6931",
                "#4d285e", "#bf953c", "#cc9acd", "#536840", "#74372c", "#c9d19d",
                "#363638", "#c69085"],

}

class Selector(object):

    def __init__(self, samples = []):
        self.samples = samples
        self.global_options = None
        self.options = None
        self._sample_sets = None

    @classmethod
    def from_dict(cls, d, opts):
        selector = cls()
        if '_:_' in d:
            global_options = d.pop('_:_')
        else:
            global_options = {}
        selector.samples = d
        selector.global_options = global_options
        selector.options = opts
        return selector

    def to_dict(self):
        return { 'samples': self.samples }


    @classmethod
    def load(cls, yaml_text):
        d = yaml.load( yaml_text )
        selector = cls.from_dict( d )
        return selector

    def dump(self):
        d = self.to_dict()
        return yaml.dump( d )


    def get_sample_ids(self, db):
        """ return sample ids; db is SQLa dbsession handler """
        pass


    def spec_to_sample_ids(self, spec_list, dbh, sample_ids=None):

        global_ids = set()
        for spec in spec_list:

            # initial spec
            ids = set()

            if 'query' in spec:

                if '$' in spec['query']:
                    raise RuntimeError('cannot process differentiating query')

                if 'batch' in spec:
                    query = spec['batch'] + '[batch] & (' + spec['query'] + ')'

                ids.update( query2set( parse_querycmd( query ) ) )

            elif 'codes' in spec:

                batch = dbh.get_batch(spec['batch'])
                ids.update( set(batch.get_sample_ids_by_codes( spec['codes'] )) )

            elif 'ids' in spec:
                ids.update( set(spec['ids']) )

            elif 'batch' in spec:
                batch = dbh.get_batch(spec['batch'])
                ids.update( batch.sample_ids )

            elif 'batch_id' in spec:
                batch = dbh.get_batch_by_id(spec['batch_id'])
                ids.update( batch.sample_ids )

            else:
                raise RuntimeError(
                    'sample spec format is incorrect, mandatory fields must exist!')

            # filtering spec

            q = dbh.session().query(dbh.Sample.id).filter(dbh.Sample.id.in_(ids))

            if 'category' in spec:
                q = q.filter(dbh.Sample.category == int(spec['category']))
            if 'int1' in spec:
                q = q.filter(dbh.Sample.int1 == int(spec['int1']))
            if 'int2' in spec:
                q = q.filter(dbh.Sample.int2 == int(spec['int2']))

            q = self.filter_sample(spec, dbh, q)

            ids = set(x.id for x in q)

            global_ids.update( ids )

        if sample_ids is not None:
            assert type(sample_ids) is set, "Please provide sample_ids as set"
            global_ids = global_ids.intersection( sample_ids )

        return global_ids


    def get_sample_sets(self, dbh, sample_ids=None):
        """ return a SampleSetContainer() """

        if not self._sample_sets:

            assert dbh, "dbh must be specified"

            sample_sets = SampleSetContainer()

            if type(self.samples) == list:
                sample_sets.append(
                    SampleSet(label = '-', colour = 'blue',
                        sample_ids = self.spec_to_sample_ids(self.samples, dbh, sample_ids)
                    )
                )

            elif type(self.samples) == dict:

                print('colour scheme:', self.options['colour_scheme'])
                colours = cycle( colour_scheme[self.options['colour_scheme']])

                for label in self.samples:
                    sample_sets.append(
                        SampleSet(label = label, colour = next(colours),
                            sample_ids = self.spec_to_sample_ids(self.samples[label],
                                                        dbh, sample_ids)
                        )
                    )

            self._sample_sets = sample_sets

        return self._sample_sets


    def filter_sample(self, spec_list, dbh, q):
        """ please override this method as necessary"""
        return q


class Filter(object):


    def __init__(self):
        self.markers = []
        self.panel_ids = None
        self.marker_ids = None
        self.species = None
        self.abs_threshold = 0      # includes alelles above rfu
        self.rel_cutoff = 0.0         # excludes alleles above % of highest rfu [ rel_threshold < height < rel_cutoff ]
        self.sample_qual_threshold = 0.0    # includes samples with marker more than %
        self.marker_qual_threshold = 0.0    # includes markers with sample more than %
        self.sample_options = None


    @classmethod
    def from_dict(cls, d, opts):
        params = cls()
        params.options = opts
        params.markers = d.get('markers', None)
        params.marker_ids = d.get('marker_ids', None)
        params.panel_ids = d.get('panel_ids', None)
        params.abs_threshold = int( d['abs_threshold'] )
        params.sample_qual_threshold = float( d['sample_qual_threshold'] )
        params.marker_qual_threshold = float( d['marker_qual_threshold'] )
        params.sample_filtering = d.get('sample_filtering', 'N')
        return params


    def get_marker_ids(self, dbh=None):
        """ return marker ids;  """
        # self.markers is name
        if (self.marker_ids is None and self.markers) and dbh:
            # only execute below if dbh is provided, marker_ids is empty and
            # markers is not empty
            markers = [ dbh.get_marker(name) for name in self.markers ]
            self.marker_ids = [ marker.id for marker in markers ]
        return self.marker_ids


    def to_dict(self):
        pass


    @staticmethod
    def load(yaml_text):
        pass

    def dump(self):
        pass


    def get_analytical_sets(self, sample_sets, marker_ids=None ):

        sets = []
        if marker_ids == None:
            marker_ids = self.get_marker_ids()
        for sample_set in sample_sets:
            sets.append( sample_set.get_analytical_set( marker_ids = marker_ids,
                                allele_absolute_threshold = self.abs_threshold,
                                allele_relative_threshold = self.rel_threshold,
                                allele_relative_cutoff = self.rel_cutoff,
                                unique = (self.sample_options == 'U') ) )

        return sets
