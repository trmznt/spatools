
from spatools.lib.utils import cout, cerr, cexit, detect_buffer


import sys, argparse, yaml, os, transaction
from io import StringIO


def init_argparser(p = None):

    if p is None:
        p = argparse.ArgumentParser('spatools dbmgr')

    # commands that modify database

    p.add_argument('--initbatch', default=False, action='store_true',
            help = 'create initial bin')

    p.add_argument('--uploadsamples', default=False, action='store_true',
            help = 'upload sample')

    p.add_argument('--importpanels', default=False, action='store_true',
            help = 'upload panel')

    p.add_argument('--uploadgenotypes', default=False, action='store_true',
            help = 'upload sample')

    p.add_argument('--createpca', default=False, action='store_true',
            help = 'create a PCA plot')

    # options

    p.add_argument('--group', default=False,
            help = 'group')

    p.add_argument('-b', '--batch', default=False,
            help = 'batch code')

    p.add_argument('--assayprovider', default='',
            help = 'assay provider vendor/group')

    p.add_argument('--species', default='',
            help = 'species of markers')

    p.add_argument('--infile', default='',
            help = 'input file')

    # db update related

    p.add_argument('--commit', default=False, action='store_true',
            help = 'commit to database')

    p.add_argument('--test', default=False, action='store_true',
            help = 'perform test, print error as warning')

    p.add_argument('--abort', default=False, action='store_true',
            help = 'abort for any warning')

    return p


def main( args, dbh=None ):

    cerr('spatools dbmgr')

    if not args.test and args.commit :
        with transaction.manager:
            do_dbmgr(args, dbh)
            cerr('** COMMIT to database **')

    else:
        cerr('WARNING -- running without commiting to database!')
        if not args.test:
            keys = input('Do you want to continue [y/n]? ')
            if not keys.lower().strip().startswith('y'):
                sys.exit(1)

        do_dbmgr(args, dbh)


def do_dbmgr( args, dbh = None, warning = True ):

    if not dbh:
        dbh = get_dbhandler(args, initial = args.initdb)

    if args.initbatch is not False:
        do_initbatch(args, dbh)

    elif args.uploadsamples is not False:
        do_uploadsamples(args, dbh)

    elif args.uploadgenotypes is not False:
        do_uploadgenotypes(args, dbh)

    elif args.importpanels is not False:
        do_importpanels(args, dbh)

    elif args.createpca is not False:
        do_createpca(args, dbh)

    else:
        cerr('WARN: command not specified!')


def do_initbatch(args, dbh):

    b = dbh.Batch()
    b.code = args.batch
    b.species = args.species
    b.public = 0
    if not args.assayprovider:
        cexit('ERR: please provide assayprovider')
    b.assay_provider_id = dbh.get_group(args.assayprovider).id
    if not args.group:
        cexit('ERR: please provide group')
    b.group_id = dbh.get_group(args.group).id
    b.lastuser_id = 1
    dbh.session.add(b)
    cout('INFO: batch %s added.' % b.code)


def do_uploadsamples(args, dbh):

    # search for batch
    if not args.batch:
        cexit('ERR: please provide batch code')

    batch = dbh.Batch.search(args.batch, dbh.session())
    cerr('INFO: using batch [%s]' % batch.code)

    name, ext = os.path.splitext( args.infile )
    if ext.lower() in [ '.csv', '.tab', '.tsv' ]:

        # convert to dictionary
        infile = open(args.infile)
        buf, delim = detect_buffer( infile.read() )

        try:
            ## the csv2dict function has to be sample-specific method
            ## use batch.Sample.csv2dict() ??
            samples, errlog, codes = batch.get_sample_class().csv2dict(
                            StringIO(buf),
                            with_report=True,
                            delimiter = delim )
        except:
            raise


    elif ext.lower() in [ '.json', '.yaml', '.yml' ]:
        payload = yaml.load( open( args.infile) )
        sample_codes = payload['codes']
        dict_samples = payload['samples']

    else:
        cexit('E: unknown extension file!')

    #print(dict_samples)    

    # insert sample dicts to target batch

    inserts = 0
    updates = 0
    option = 'A'

    # updating location first
    null_location = dbh.search_location(auto=True)
    session = dbh.session()

    with session.no_autoflush:

      #for (sample_code, dict_sample) in samples.items():
      for sample_code in codes:
        dict_sample = samples[sample_code]
        # check sanity
        #if sample_code != sample['code']:
        #    pass

        db_sample = batch.search_sample( sample_code )

        if option == 'A':
            if not db_sample:
                db_sample = batch.add_sample( sample_code )
                db_sample.location = null_location
                inserts += 1
            else:
                updates += 1

        elif option == 'U':
            if not db_sample:
                continue
            updates += 1

        elif option == 'N':
            if db_sample: continue
            db_sample = batch.add_sample( sample_code )
            db_sample.location = null_location
            inserts += 1

        else:
            return error_page('Invalid option')
        db_sample.update( dict_sample )
        cerr('Flushing sample: %s' % db_sample.code)
        session.flush([db_sample])

    cerr("Updating %d samples, inserting %d samples" % (updates, inserts))


def do_uploadgenotypes(args, dbh):

    # search for batch
    if not args.batch:
        cexit('ERR: please provide batch code')

    batch = dbh.Batch.search(args.batch, dbh.session())
    cerr('INFO: using batch [%s]' % batch.code)

    name, ext = os.path.splitext( args.infile )
    if ext.lower() in [ '.csv', '.tab', '.tsv', '.txt' ]:

        # convert to dictionary
        infile = open(args.infile)
        buf, delim = detect_buffer( infile.read() )

        try:
            ## the csv2dict function has to be sample-specific method
            ## use batch.Sample.csv2dict() ??
            genotypes, errlog, codes = dbh.Genotype.csv2dict(
                            StringIO(buf),
                            with_report=True,
                            delimiter = delim )
        except ValueError as err:
            return error_page(request,  'ValueError: {0}'.format(err) )


    elif ext.lower() in [ '.json', '.yaml', '.yml' ]:
        payload = yaml.load( open( args.infile) )
        codes = payload['codes']
        genotypes = payload['genotypes']

    exists = not_exists = 0
    assay_set = {}

    for sample_code in genotypes:

        genotype_set = genotypes[sample_code]


        # search samples
        sample = batch.search_sample(sample_code)
        if not sample:
            cerr('WARN: sample not found: %s' % sample_code)
            not_exists += 1
            continue


        exists += 1

        # set the genotype
        for (assay_code, assay_data) in genotype_set['assays'].items():
            print(assay_code)
            if assay_code not in assay_set:

                assay = dbh.get_locus_by_code(assay_code)
                if not assay:

                    # create and flush assay
                    assay = dbh.Locus(code=assay_code, refseq=assay_data['refseq'], position=assay_data['position'])
                    dbh.session().add( assay )
                    dbh.session().flush([assay])

                assay_set[assay_code] = assay
                cerr('INFO: creating new assay [%s]' % assay.code)

            else:
                assay = assay_set[assay_code]

            genotype = dbh.Genotype(sample_id = sample.id, locus_id = assay.id,
                        A = assay_data['A'], C = assay_data['C'], T = assay_data['T'], G = assay_data['G'])
            genotype.call, genotype.raw_qual = basecall(assay_data)
            dbh.session().add( genotype )

        dbh.session().flush()

    cerr('WARN: assays %d' % len(assay_set))

    cerr('INFO: found %d samples, not found %s samples' % (exists, not_exists))

    #import pprint
    #pprint.pprint(genotypes)

    cerr('INFO: Parsing %s samples' % len(genotypes))


def do_importpanels(args, dbh):

    if not args.infile:
        cexit('ERR: please provide yaml input file')

    d = yaml.load( open(args.infile) )
    panel_specs = d['panels']

    for panel_code, panel_spec in panel_specs.items():
        loci_pos = panel_spec['loci']
        loci = [ dbh.get_locus(refseq, pos)  for refseq, pos in loci_pos ]
        panel = dbh.Panel()
        panel.code = panel_code
        dbh.session().add(panel)
        for locus in loci:
            panel.loci.append( locus )
        cerr('[INFO: panel %s has been added with %d loci ]' % (panel.code, len(panel.loci)))


def basecall( assay_data ):

    l = [ (assay_data['A'], 'A'), (assay_data['C'], 'C'), (assay_data['T'], 'T'), (assay_data['G'], 'G')]
    l.sort(reverse=True)
    total = sum( v[0] for v in l )
    q = l[0][0]/total if total > 0 else 0
    if total < 25:
        base = '-'
    else:
        base = l[0][1] if q > 0.05 else 'N'
    return l[0][1], q 

    import IPython
    IPython.embed()

class V:
    pass

def do_createpca(args, dbh):

    """ a shortcut to create PCA from all samples based on country """

    df = dbh.get_allele_dataframe(None, None, None)
    import pandas

    variant_df = pandas.pivot_table( df, index = 'sample_id', columns = 'locus_id', values='call',
                aggfunc = lambda x: x )

    from spatools.lib.analytics import dist
    from spatools.lib.analytics import ca

    D = dist.simple_distance(variant_df)

    DM = V()
    DM.M = D[0]

    res = ca.pcoa( DM )

    import matplotlib.pyplot as plt
    axis = [ (0, 39), (40, 59), (60, 71), (72, 85), (86, 125), (126, 131) ]

    fig = plt.figure()
    ax = fig.add_subplot(111)

    pca_matrix = res[0]
    pca_var = res[1]

    for (i1, i2) in axis:
        ax.scatter( pca_matrix[i1:i2, 0], pca_matrix[i1:i2, 1] )
        
    fig.savefig('test.png')


    #import IPython
    #IPython.embed()
