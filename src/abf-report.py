#!/usr/bin/env python3
# encoding: utf-8
"""
abf-report -- reports on ABF files

@author:     Jason White

@copyright:  2019 FBRI. All rights reserved.

@license:    AS IS

@contact:    jas0nw@vtc.vt.edu
@deffield    updated: 2019-07-23
"""

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import os
import sys
import traceback
import pandas as pd

from hive.report.abfstats import ABFReporter

__all__ = []
__version__ = 0.1
__date__ = '2019-07-23'
__updated__ = '2019-07-23'
__verbose__ = 0


class CLIError(Exception):
    """Generic exception to raise and log different fatal errors."""

    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = f'error: {msg}'

    def __str__(self):
        return self.msg

    def __unicode__(self):
        return self.msg


def __log(message, test=None):
    global __verbose__

    # default to logging when verbose
    if test is None:
        test = (__verbose__ > 0)

    if test:
        print(message, flush=True)


def main(_argv=None):  # IGNORE:C0111
    """Command line options."""
    global __verbose__

    if _argv is None:
        # argv = sys.argv
        pass
    else:
        sys.argv.extend(_argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = 'v%s' % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split('\n')[1]
    program_license = '''%s

  Created by Jason White on %s.
  Copyright 2019 FBRI. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an 'AS IS' basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license,
                                formatter_class=RawDescriptionHelpFormatter)

        # parser.add_argument('-v', '--verbose', dest='verbose', action='count', default=0,
        #                     help='increase verbosity level')

        parser.add_argument('--version', action='version',
                            version=program_version_message)

        # parser.add_argument('-o', '--output', type=str, nargs='?', dest='output', default=None,
        #                     help='output file, or directory for multiple input files [default: infile.h5]')

        # parser.add_argument('-c', '--channel', type=str, nargs='?', dest='channels', action='append',
        #                     help='channel to convert: can be either number or ADC name [default: all]')

        # parser.add_argument('--overwrite', dest='overwrite', action='store_true',
        #                     help='overwrite existing output file(s)')

        parser.add_argument('-i', '--input', dest='file_or_dir', type=str, nargs='?', default='.',
                            help='path to source file or directory (default = ".")')

        parser.add_argument('-p', '--pattern', dest='pattern', type=str, nargs='?', default='*.abf',
                            help='ABF file pattern to match (default = "*.abf")')

        parser.add_argument('-r', '--recurse', dest='recurse', action='store_true', default=False,
                            help='search in subdirectories?')

        parser.add_argument('-o', '--output', dest='csv_file', type=str, nargs='?', default='abf-report.csv',
                            help='output CSV file (default = "abf-report.csv"')

        # Process arguments
        args = parser.parse_args()

        _input = args.file_or_dir
        _pattern = args.pattern
        _recurse = args.recurse
        _output = args.csv_file

        __verbose__ = 1  # args.verbose

        converter = ABFReporter(
            input_path=_input,
            file_pattern=_pattern,
            recurse=_recurse)

        df: pd.DataFrame = converter.process().data_frame
        df.to_csv(_output, float_format='%0.1f', index=False)
        __log(f"*** DONE: wrote {df.shape[0]} lines to {_output}")

    except KeyboardInterrupt:
        print('*** INTERRUPT ***')
        return 0

    except CLIError as e:
        indent = len(program_name) * ' '
        sys.stderr.write(program_name + ': ' + e.msg + '\n')
        sys.stderr.write(indent + '  for help use --help\n')
        return 2

    except Exception as e:
        indent = len(program_name) * ' '
        sys.stderr.write(program_name + ': ' + repr(e) + '\n')
        traceback.print_exc()
        sys.stderr.write(indent + '  for help use --help\n')
        return 2

    return 0


if __name__ == '__main__':
    sys.exit(main())
