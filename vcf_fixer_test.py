import vcf_fixer

from itertools import ifilter
from nose.tools import *


# Test helper methods
def get_columns(vcf_data):
    '''Returns a list of columns in the VCF file.'''
    lines = vcf_data.split('\n')
    def is_field_names_line(line):
        return line.startswith('#') and not line.startswith('##')

    header_line = next(ifilter(is_field_names_line, lines))
    headers = header_line[1:].split('\t')
    return headers


def tabs_per_line(data):
    '''Returns a list of the number of tabs in each line of the data.

    Ignores lines beginning with ##.
    '''
    return [len(x.split('\t')) for x in
            ifilter(lambda x: not (x.startswith('##') or x == ''),
                   data.split('\n'))]

def test_tabs_per_line():
    eq_([1,2,3], tabs_per_line('##foo\n#bar\nbaz\tquux\nout\tof\twords\n'))


def test_get_columns():
    vcf = '##hello\n#column1\tcolumn2\nvalue1\tvalue2\n'
    eq_(['column1', 'column2'], get_columns(vcf))


def test_fix():
    broken_vcf = open('testdata/run19.vcf').read()
    eq_(['CHROM', 'POS', 'ID', 'REF', 'ALT', 'QUAL', 'FILTER', 'INFO'],
            get_columns(broken_vcf))
    eq_(set([8, 9]), set(tabs_per_line(broken_vcf)))

    fixed_vcf = vcf_fixer.fix(broken_vcf)
    golden_vcf = open('testdata/run19.fixed.vcf').read()
    eq_(golden_vcf, fixed_vcf)
