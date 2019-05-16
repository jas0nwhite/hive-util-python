'''
Created on May 15, 2019

@author: jwhite
'''

from abc import ABC, abstractmethod
from pathlib import Path
import os
from dfply import *  # @UnusedWildImport


class FileConverter(ABC):
    '''
    Base class for file format conversion
    '''

    def __init__(self, input_file, output_file=None, verbose=False, suffix='.out'):
        """
        Constructs a new LVMConverter
        @param input_file: the input file path
        @param output_file: the output file path
            defaults to input file with extension replaced with suffix
        @param verbose: boolean governing output verbosity
        @param suffix: suffix to use for default output filename
        """
        self.__input_file = input_file
        self.__verbose = verbose

        inpath = Path(input_file)

        if output_file is None:
            self.__output_file = str(inpath.with_suffix(suffix))
        elif os.path.isdir(output_file):
            self.__output_file = str(Path(output_file) / inpath.with_suffix(suffix).name)
        else:
            self.__output_file = output_file

    @property
    def input_file(self):
        """
        The file path of the input
        """
        return self.__input_file

    @property
    def output_file(self):
        """
        The file path of the output
        Defaults to the input file path with extension replaced with suffix
        """
        return self.__output_file

    @property
    def verbose(self):
        """
        If true, print out processing details, like timing
        """
        return self.__verbose

    @make_symbolic
    def __combine_date_time(self, date_s, time_s):
        # [dfply] Combines date part of one series with time part of other series
        # @param date_s: date series
        # @param time_s: time series
        return time_s + (date_s - time_s.dt.normalize())

    @make_symbolic
    def __as_string(self, series, format_string='{}'):
        # [dfply] Formats given series using given string format
        # @param series: the series to format
        # @param format_string: the format to apply to the series
        return series.map(format_string.format)

    @make_symbolic
    def __as_int(self, series):
        # [dfply] Converts the given series to an int series
        # @param series: the series to convert
        return series.astype(int)

    @abstractmethod
    def process(self):
        pass
