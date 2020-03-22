
# calculate R^2 for LD, and create heatmap plot


def calculate_r2(analytical_set):

	# prepare genotype array as no_of_alternate_allele
	#
	#    	sample1 sample2 sample3
	# snp1
	# snp2
	# snp3
	# snp4
	# snp5

	genotype_df = analytical_set.variant_df.transpose()
	genotype_mat = genotype_df.as_matrix()

	raise RuntimeError()