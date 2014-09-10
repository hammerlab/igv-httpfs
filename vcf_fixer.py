#!/usr/bin/env python
'''The VCF files output by Guacamole are malformed. This fixes them.

See https://github.com/bigdatagenomics/adam/issues/353 for details.

The fix is to add "FORMAT" and "somatic" columns.
'''

def fix(vcf_contents):
    out = []
    for line in vcf_contents.split('\n'):
        if line.startswith('##'):
            pass  # Don't modify comment lines
        elif line.startswith('#'):
            line += '\tFORMAT\tsomatic'
        elif line == '':
            pass  # most likely a trailing newline
        else:
            line += '\t1/0'
        out.append(line)

    return '\n'.join(out)
