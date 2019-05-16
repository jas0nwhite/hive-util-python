#!/usr/bin/env python3
# encoding: utf-8
'''
lvm2hd5 -- converts LVM to HD5 for opm-MEG

@author:     Jason White

@copyright:  2018 VTCRI. All rights reserved.

@license:    AS IS

@contact:    jas0nw@vtc.vt.edu
@deffield    updated: Updated
'''

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import os
import sys

from hive.convert.lvm2h5 import LVMConverter
from hive.timer import Timer

__all__ = []
__version__ = 1.0
__date__ = '2018-09-07'
__updated__ = '2018-09-07'
__verbose__ = 0


class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''

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


def __log(message, level=1):
    global __verbose__
    if __verbose__ >= level:
        print(message, flush=True)


def main(argv=None):  # IGNORE:C0111
    '''Command line options.'''
    global __verbose__

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = sys.argv[0]
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
                            help='output file, or directory for multiple input files [default: infile.h5]')

        parser.add_argument('--overwrite', dest='overwrite', action='store_true',
                            help='overwrite existing output file(s)')

        parser.add_argument(dest='paths', type=str, nargs='+', metavar='infile.lvm',
                            help='paths to source file(s)')

        # Process arguments
        args = parser.parse_args()

        paths = args.paths
        __verbose__ = args.verbose
        overwrite = args.overwrite
        output = args.output

        if not __check_output_arg(paths, output):
            return 1

        if overwrite:
            __log('Overwrite mode on')

        for inpath in paths:
            converter = LVMConverter(inpath, output_file=output,
                                     verbose=(__verbose__ > 1))

            if __check_output_file(paths, converter.output_file, overwrite):
                __log(f'{converter.input_file} -> {converter.output_file}')
                with Timer(f'{converter.input_file} -> {converter.output_file}', (__verbose__ > 0)):
                    converter.process()
            else:
                __log(f'{converter.input_file} -> *** SKIP ***')

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
        sys.stderr.write(indent + '  for help use --help\n')
        return 2


if __name__ == "__main__":
    sys.exit(main())
