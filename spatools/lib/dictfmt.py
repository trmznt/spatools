
import csv, json, os
from math import ceil

genotype_csv_header = { 'SAMPLE', 'ASSAYCODE', 'CHR', 'POS', 'A', 'T', 'C', 'G' }

def check_csv_headers(fieldnames, csv_headers):

    err_log = []

    # check field names
    if 'SAMPLE' not in fieldnames:
        raise RuntimeError( 'WARNING: SAMPLE not in the header! '
                            'Please check that SAMPLE is the header of your file and verify that'
                            'the extension of the file matches with the delimiter character used in the file.')

    for fieldname in fieldnames:
        if fieldname not in csv_headers:
            err_log.append('Header not recognized: %s' % fieldname)
            #raise RuntimeError('CSV headers not recognized: %s' % fieldname)

    return err_log


def reader_from_stream( istream, headers, delimiter ):

    reader = csv.DictReader( istream, delimiter = delimiter )
    errlog = check_csv_headers( reader.fieldnames, headers )

    return (reader, errlog)


def genotype_csv2dict(istream, with_report=False, delimiter='\t'):

    (reader, errlog) = reader_from_stream( istream, genotype_csv_header, delimiter )
    #log = StringIO() if with_report else None

    return parse_genotype_csv( reader, errlog )


def text_to_float(text):
	if text.lower() == 'na':
		return 0
	return float(text)

def parse_genotype_csv( reader, log, sample_func = None, existing_samples = None ):

    counter = 1

    samples = existing_samples or {}
    sample_codes = existing_samples.keys() if existing_samples else []
    assay_codes = []

    for row in reader:

    	counter += 1
    	name = row['SAMPLE']

    	if name in samples:
    		sample = samples[name]

    	else:
    		sample = { 'code': name, 'assays': {} }
    		samples[name] = sample
    		sample_codes.append( name )

    	assay_code = row['ASSAY']
    	if assay_code not in assay_codes:
    		assay_codes.append(assay_code)

    	sample['assays'][assay_code] = {
    		'refseq': row['REFSEQ'],
    		'position': int(row['POS']),
    		'A': ceil( text_to_float(row['A']) * 1000),
    		'T': ceil( text_to_float(row['T']) * 1000),
    		'C': ceil( text_to_float(row['C']) * 1000),
    		'G': ceil( text_to_float(row['G']) * 1000),
    	}

    return samples, log, sample_codes

