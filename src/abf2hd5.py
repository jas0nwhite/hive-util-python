#!/usr/bin/env python3
# encoding: utf-8
"""
abf2hd5 -- converts ABF to HDF5 for voltammetry

@author:     Jason White

@copyright:  2019 FBRI. All rights reserved.

@license:    AS IS

@contact:    jas0nw@vtc.vt.edu
@deffield    updated: Updated
"""

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import os
from pathlib import Path
import sys
import traceback

from hive.convert.abf2h5 import ABFConverter
from hive.timer import Timer

__all__ = []
__version__ = 1.0
__date__ = '2019-05-16'
__updated__ = '2019-07-24'
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


def __check_output_file(paths, output, overwrite):
    assert (output is not None and len(output) > 0), (
        'invalid output directory [{str(output)}]')
    assert len(paths) > 0, 'empty input path list'

    if not overwrite:
        # one input file + not overwrite => output file must not exist
        if os.path.isfile(output):
            return False
        else:
            return True
    else:
        return True


def __check_output_arg(paths, output):
    if len(paths) > 1 and output is not None:
        # output argument must be a directory
        if not os.path.isdir(output):
            raise(
                CLIError(f'multiple input files: directory "{output}" does not exist'))

    return True


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

        parser.add_argument('-v', '--verbose', dest='verbose', action='count', default=0,
                            help='increase verbosity level')

        parser.add_argument('--version', action='version',
                            version=program_version_message)

        parser.add_argument('-o', '--output', type=str, nargs='?', dest='output', default=None,
                            help='output file, or directory for multiple input files [default: FILE.h5]')

        parser.add_argument('-c', '--channel', type=str, nargs='?', dest='channels', action='append', metavar="CHANNEL",
                            help='channel to convert: can be either number or ADC name [default: all]')

        parser.add_argument('--overwrite', dest='overwrite', action='store_true',
                            help='overwrite existing output file(s)')

        parser.add_argument(dest='paths', type=str, nargs='+', metavar='FILE.abf',
                            help='paths to source file(s)')

        # Process arguments
        args = parser.parse_args()

        paths = args.paths
        __verbose__ = args.verbose
        overwrite = args.overwrite
        output = args.output
        channels = args.channels

        if not __check_output_arg(paths, output):
            return 1

        if overwrite:
            __log('Overwrite mode on')

        for inpath in paths:
            converter = ABFConverter(
                inpath,
                output_file=output,
                channel_select=channels,
                verbose=(__verbose__ > 1))

            src_file = Path(converter.input_file).name
            dst_file = Path(converter.output_file).name

            if __check_output_file(paths, converter.output_file, overwrite):
                __log(f'{src_file} -> {dst_file}', (__verbose__ == 1))
                with Timer(f'{src_file} -> {dst_file}', (__verbose__ > 1)):
                    converter.process()
            else:
                __log(f'{src_file} -> *** SKIP ***')

        if len(paths) > 1:
            __log('*** DONE ***')
        return 0
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


if __name__ == '__main__':
    sys.exit(main())
