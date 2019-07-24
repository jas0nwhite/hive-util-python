# -*- coding: utf-8 -*-
"""
Created on Thu Sep  6 20:40:14 2018

@author: jwhite

Converter for opm-MEG LVM files to H5 databases
"""
import shutil
from dfply import *

from hive.convert.base import FileConverter
from hive.timer import Timer


class LVMConverter(FileConverter):

    def __init__(self, input_file, output_file=None, verbose=False):
        """
        Constructs a new LVMConverter
        @param input_file: the input file path
        @param output_file: the output file path
            defaults to input file with extension replaced with .h5
        @param verbose: boolean governing output verbosity
        """
        super().__init__(input_file, output_file, verbose, suffix='.h5')

    def process(self):
        """
        Do the conversion work
        """

        # =========================================================================
        # read data from LVM file
        # =========================================================================
        with Timer(f'read {self.input_file}', verbose=self.verbose):
            # first, we read in the header portion
            hdr = pd.read_csv(self.input_file,
                              sep='\t',
                              skiprows=14,
                              nrows=7,
                              header=None)

            # next, we re-shape the header to a table of channel attributes
            seconds = pd.Timedelta(seconds=1.0)

            header = (
                    hdr >>
                    gather('channel', 'value', columns_from(1)) >>
                    spread(0, X.value, convert=True) >>
                    mask(X.Samples > 0) >>
                    mutate(channel=X.channel - colmin(X.channel)) >>
                    mutate(offset=(X.Time - colmin(X.Time)) / seconds) >>
                    mutate(start=self.__combine_date_time(X.Date, X.Time)) >>
                    mutate(name=self.__as_string(X.channel, format_string='ch{:03d}')) >>
                    mutate(Samples=self.__as_int(X.Samples)) >>
                    select(
                        X.channel,
                        X.name,
                        X.offset,
                        X.start,
                        X.Samples,
                        X.Y_Unit_Label,
                        X.X_Dimension,
                        X.X0,
                        X.Delta_X) >>
                    arrange(X.channel)
            )

            # next, we load in the actual data (n_obvs x n_chan)
            dat = pd.read_csv(self.input_file, sep='\t', skiprows=22)

            # now, let's replace the dummy name we created in the
            # header above with the actual channel name from the
            # column names
            header['name'] = dat.columns.drop(['X_Value', 'Comment'])

        # =========================================================================
        # reshape the data
        # =========================================================================
        with Timer(f'arrange {self.input_file}', verbose=self.verbose):
            # select only the channels we want: cuts down on memory and processing
            channels = (
                    header >>
                    select(X.channel, X.name, X.offset)
            )

            # here's where we re-arrange
            data = (
                    dat >>
                    mutate(frame=row_number(X.X_Value)) >>
                    mutate(frame=self.__as_int(X.frame)) >>
                    drop(X.Comment) >>
                    gather('name', 'Y_Value', starts_with('cDAQ')) >>
                    inner_join(channels, by='name') >>
                    mutate(time=X.X_Value + X.offset) >>
                    select(X.channel, X.frame, X.time, X.Y_Value)
            )

        # =========================================================================
        # write data to H5 file
        # =========================================================================
        with Timer(f'write {self.output_file}', verbose=self.verbose):
            header.to_hdf(
                self.output_file,
                mode='w',
                format='table',
                key='header',
                complib='zlib',
                complevel=9,
                data_columns=True,
                index=False
            )

            # ...and a table for each channel
            for chan in channels['channel']:
                ch = (
                        data >>
                        mask(X.channel == chan) >>
                        arrange(X.frame)
                )

                ch.to_hdf(
                    self.output_file,
                    mode='r+',
                    format='table',
                    key=f'data/ch{chan:03d}',
                    complib='zlib',
                    complevel=9,
                    data_columns=True,
                    index=False
                )

            # copy permissions, times, etc. from original file
            shutil.copystat(self.input_file, self.output_file)
