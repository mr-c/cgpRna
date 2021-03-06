"""
Handle the command line parsing and select the correct sub process.
"""

import argparse
import sys
import pkg_resources  # part of setuptools

from .map import map_seq_files
from .mapping_stats import generate_stats
from .htseq_count import count
from .bigwig import generate_bigwig
from .fusion_tools import tophat_fusion, star_fusion, defuse

version = pkg_resources.require("run_cgprna")[0].version


def main():
    """
    Sets up the parser and handles triggereing of correct sub-command
    """
    common_parser = argparse.ArgumentParser('parent', add_help=False)
    common_parser.add_argument('-v', '--version',
                               action='version',
                               version='%(prog)s ' + version)

    parser = argparse.ArgumentParser(prog='run-cgprna', parents=[common_parser])

    subparsers = parser.add_subparsers(help='sub-command help')

    # mapping arguments
    parser_a = subparsers.add_parser(
        'map',
        parents=[common_parser],
        description='Use STAR to map RNA-Seq reads to a reference genome',
        epilog='Input can be either bam or \'f(ast)?q(\.gz)?\'.')
    parser_a.add_argument(
        '-i', '--input', dest='input',
        metavar='FILE',
        nargs='+',
        help='An input raw bam file, or a pair of FastQ files split with spaces. (optionally gzip compressed).',
        required=True)
    parser_a.add_argument(
        '-r', '--reference', dest='ref',
        metavar='TAR|PATH',
        help='A reference bundle tar file or the path to reference root directory.',
        required=True)
    parser_a.add_argument(
        '-s', '--sample-name', dest='sample_name',
        metavar='STR',
        help='Sample name, which will used to prefix output file names and SM tag in the BAM file header.',
        required=True)
    parser_a.add_argument(
        '-sp', '--species', dest='species',
        metavar='STR',
        help='Species name. No need to set if using a pre-built reference bundle. If using a folder path as the value of \'--reference\', it\' be used to locate reference files.',
        required=False)
    parser_a.add_argument(
        '-rb', '--reference-build', dest='ref_build',
        metavar='STR',
        help='Reference build name. No need to set if using a pre-built reference bundle. If using a folder path as the value of \'--reference\', it\' be used to locate reference files.',
        required=False)
    parser_a.add_argument(
        '-gb', '--gene-build', dest='gene_build',
        metavar='STR',
        help='Gene build name. No need to set if using a pre-built reference bundle. If using a folder path as the value of \'--reference\', it\' be used to locate for GTF file.',
        required=False)
    parser_a.add_argument(
        '-gtf', '--gene-build-gtf-name', dest='gene_build_gtf_name',
        metavar='STR',
        help='File name of the gene build annotaion file. No need to set if using a pre-built reference bundle. If using a folder path as the value of \'--reference\', it\' be used to locate the GTF file.',
        required=False)
    parser_a.add_argument(
        '-od', '--output-directory', dest='out_dir',
        metavar='DIR', default='.',
        help='Output directory. Default: current directory.',
        required=False)
    parser_a.add_argument(
        '-op', '--output-file-prefix', dest='out_file_prefix',
        metavar='STR',
        help='Output file name prefix. Default: value of --sample-name.',
        required=False)
    parser_a.add_argument(
        '-t', '--threads', dest='threads',
        metavar='INT', type=int, default=1,
        help='Number of threads to use.',
        required=False)
    parser_a.add_argument(
        '--rg-id-tag', dest='rg_id_tag',
        metavar='STR',
        help='Readgroup ID tag value in the output BAM. Default: "1" or taken from the first input raw BAM file.',
        required=False)
    parser_a.add_argument(
        '--lb-tag', dest='lb_tag',
        metavar='STR',
        help='Sequencing library tag value in the output BAM header. Default: None or taken from the input raw BAM file.',
        required=False)
    parser_a.add_argument(
        '--ds-tag', dest='ds_tag',
        metavar='STR',
        help='Description tag value in the output BAM header. Default: None or taken from the input raw BAM file.',
        required=False)
    parser_a.add_argument(
        '--pl-tag', dest='pl_tag',
        metavar='STR',
        help='Platform tag value in the output BAM header. Default: None or taken from the input raw BAM file.',
        required=False)
    parser_a.add_argument(
        '--pu-tag', dest='pu_tag',
        metavar='STR',
        help='Platform unit tag value in the output BAM header. Default: None or taken from the input raw BAM file.',
        required=False)
    parser_a.set_defaults(func=map_seq_files)

    # create the parser for "stats" command
    parser_b = subparsers.add_parser(
        'stats',
        parents=[common_parser],
        description='Generate mapping stats from a BAM file, with/without a BAM file in which reads were mapped to the transcriptome instead of genome.')
    parser_b.add_argument(
        '-i', '--input', dest='input',
        metavar='FILE',
        help='Input BAM file, in which reads are mapped to a reference genome (NOT transcriptome).',
        required=True)
    parser_b.add_argument(
        '-r', '--reference', dest='ref',
        metavar='TAR|PATH',
        help='A reference bundle tar file or the path to reference root directory.',
        required=True)
    parser_b.add_argument(
        '-tb', '--transcriptome-bam', dest='trans_bam',
        metavar='FILE',
        help='BAM file, in which reads are mapped to a reference transciptome (NOT genome).',
        required=False)
    parser_b.add_argument(
        '-od', '--output-directory', dest='out_dir',
        metavar='DIR', default='.',
        help='Output directory. Default: current directory.',
        required=False)
    parser_b.set_defaults(func=generate_stats)

    # create the parser for "bigwig" command
    parser_c = subparsers.add_parser(
        'bigwig',
        parents=[common_parser],
        description='Generate bigwig file from a BAM file.')
    parser_c.add_argument(
        '-i', '--input', dest='input',
        metavar='FILE',
        help='Input BAM file, in which reads are mapped to a reference genome (NOT transcriptome).',
        required=True)
    parser_c.add_argument(
        '-r', '--reference', dest='ref',
        metavar='FASTA_FILE',
        help='FASTA file of a reference, which the input BAM file was mapped to.',
        required=True)
    parser_c.add_argument(
        '-od', '--output-directory', dest='out_dir',
        metavar='DIR', default='.',
        help='Output directory. Default: current directory.',
        required=False)
    parser_c.add_argument(
        '-t', '--threads', dest='threads',
        metavar='INT', type=int, default=1,
        help='Number of threads to use.',
        required=False)
    parser_c.set_defaults(func=generate_bigwig)

    # create the parser for "count" command
    parser_d = subparsers.add_parser(
        'count',
        parents=[common_parser],
        description='Generate gene counts from a BAM file.')
    parser_d.add_argument(
        '-i', '--input', dest='input',
        metavar='FILE',
        help='Input BAM file, in which reads are mapped to a reference genome (NOT transcriptome).',
        required=True)
    parser_d.add_argument(
        '-r', '--reference', dest='ref',
        metavar='GTF_FILE',
        help='A reference GTF file.',
        required=True)
    parser_d.add_argument(
        '-od', '--output-directory', dest='out_dir',
        metavar='DIR', default='.',
        help='Output directory. Default: current directory.',
        required=False)
    parser_d.set_defaults(func=count)

    # create the parser for "tophat_fusion" command
    parser_e = subparsers.add_parser(
        'tophat-fusion',
        parents=[common_parser],
        description='Use Tophat2 to identify gene fusion events.')
    parser_e.add_argument(
        '-i', '--input', dest='input',
        metavar='FILE',
        nargs='+',
        help='Input files, can be BAM files or FastQ files or a mixture of both. File names of FastQ files much have suffix of "_1" or "_2" immediately prior to ".f[ast]q".',
        required=True)
    parser_e.add_argument(
        '-s', '--sample-name', dest='sample_name',
        metavar='STR',
        help='Sample name, which will used to prefix output file names and SM tag in the BAM file header.',
        required=True)
    parser_e.add_argument(
        '-r', '--reference', dest='ref',
        metavar='TAR|PATH',
        help='A reference bundle tar file or the path to reference root directory.',
        required=True)
    parser_e.add_argument(
        '-od', '--output-directory', dest='out_dir',
        metavar='DIR', default='.',
        help='Output directory. Default: current directory.',
        required=False)
    parser_e.add_argument(
        '-sp', '--species', dest='species',
        metavar='STR',
        help='Species name. No need to set if using a pre-built reference bundle. If using a folder path as the value of \'--reference\', it should be the name of an existing folder containing one or more folders named with differenct reference builds in \'--reference\' folder.',
        required=False)
    parser_e.add_argument(
        '-rb', '--reference-build', dest='ref_build',
        metavar='STR',
        help='Reference build name. No need to set if using a pre-built reference bundle. If using a folder path as the value of \'--reference\', it should the name of an existing folder containing \'tophat\' folder for this reference build in \'--species\' folder.',
        required=False)
    parser_e.add_argument(
        '-gb', '--gene-build', dest='gene_build',
        metavar='STR',
        help='Gene build name. No need to set if using a pre-built reference bundle. If using a folder path as the value of \'--reference\', it should be the name of an existing folder containing transcriptome index files in \'tophat\' folder.',
        required=False)
    parser_e.add_argument(
        '-t', '--threads', dest='threads',
        metavar='INT', type=int, default=1,
        help='Number of threads to use.',
        required=False)
    parser_e.set_defaults(func=tophat_fusion)

    # create the parser for "star_fusion" command
    parser_f = subparsers.add_parser(
        'star-fusion',
        parents=[common_parser],
        description='Use STAR to identify gene fusion events.')
    parser_f.add_argument(
        '-i', '--input', dest='input',
        metavar='FILE',
        nargs='+',
        help='Input files, can be BAM files or FastQ files or a mixture of both. File names of FastQ files much have suffix of "_1" or "_2" immediately prior to ".f[ast]q".',
        required=True)
    parser_f.add_argument(
        '-s', '--sample-name', dest='sample_name',
        metavar='STR',
        help='Sample name, which will used to prefix output file names and SM tag in the BAM file header.',
        required=True)
    parser_f.add_argument(
        '-r', '--reference', dest='ref',
        metavar='TAR|PATH',
        help='A reference bundle tar file or the path to reference root directory.',
        required=True)
    parser_f.add_argument(
        '-od', '--output-directory', dest='out_dir',
        metavar='DIR', default='.',
        help='Output directory. Default: current directory.',
        required=False)
    parser_f.add_argument(
        '-sp', '--species', dest='species',
        metavar='STR',
        help='Species name. No need to set if using a pre-built reference bundle. If using a folder path as the value of \'--reference\', it should be the name of an existing folder containing one or more folders named with differenct reference builds in \'--reference\' folder.',
        required=False)
    parser_f.add_argument(
        '-rb', '--reference-build', dest='ref_build',
        metavar='STR',
        help='Reference build name. No need to set if using a pre-built reference bundle. If using a folder path as the value of \'--reference\', it should the name of an existing folder containing \'star\' folder for this reference build in \'--species\' folder.',
        required=False)
    parser_f.add_argument(
        '-gb', '--gene-build', dest='gene_build',
        metavar='STR',
        help='Gene build name. No need to set if using a pre-built reference bundle. If using a folder path as the value of \'--reference\', it should be the name of an existing folder containing a GTF file in \'star\' folder.',
        required=False)
    parser_f.add_argument(
        '-t', '--threads', dest='threads',
        metavar='INT', type=int, default=1,
        help='Number of threads to use.',
        required=False)
    parser_f.set_defaults(func=star_fusion)


    # create the parser for "defuse" command
    parser_g = subparsers.add_parser(
        'defuse',
        parents=[common_parser],
        description='Use Defuse to identify gene fusion events.')
    parser_g.add_argument(
        '-i', '--input', dest='input',
        metavar='FILE',
        nargs='+',
        help='Input files, can be BAM files or FastQ files or a mixture of both. File names of FastQ files much have suffix of "_1" or "_2" immediately prior to ".f[ast]q".',
        required=True)
    parser_g.add_argument(
        '-s', '--sample-name', dest='sample_name',
        metavar='STR',
        help='Sample name, which will used to prefix output file names and SM tag in the BAM file header.',
        required=True)
    parser_g.add_argument(
        '-r', '--reference', dest='ref',
        metavar='TAR|PATH',
        help='A reference bundle tar file or the path to reference root directory.',
        required=True)
    parser_g.add_argument(
        '-od', '--output-directory', dest='out_dir',
        metavar='DIR', default='.',
        help='Output directory. Default: current directory.',
        required=False)
    parser_g.add_argument(
        '-sp', '--species', dest='species',
        metavar='STR',
        help='Species name. No need to set if using a pre-built reference bundle. If using a folder path as the value of \'--reference\', it should be the name of an existing folder containing one or more folders named with differenct reference builds in \'--reference\' folder.',
        required=False)
    parser_g.add_argument(
        '-rb', '--reference-build', dest='ref_build',
        metavar='STR',
        help='Reference build name. No need to set if using a pre-built reference bundle. If using a folder path as the value of \'--reference\', it should the name of an existing folder containing \'defuse\' folder for this reference build in \'--species\' folder.',
        required=False)
    parser_g.add_argument(
        '-gb', '--gene-build', dest='gene_build',
        metavar='STR',
        help='Gene build name. No need to set if using a pre-built reference bundle. If using a folder path as the value of \'--reference\', it should be the name of an existing folder containing all Defuse index files in \'defuse\' folder.',
        required=False)
    parser_g.add_argument(
        '-t', '--threads', dest='threads',
        metavar='INT', type=int, default=1,
        help='Number of threads to use.',
        required=False)
    parser_g.set_defaults(func=defuse)

    args = parser.parse_args()
    if len(sys.argv) > 1:
        args.func(args)
    else:
        sys.exit('\nError: missed required arguments.\n\tPlease run: run-cgprna --help\n')
