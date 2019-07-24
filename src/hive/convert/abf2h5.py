"""
Created on May 15, 2019

@author: jwhite

Converter for voltammetry ABF (Axon binary format) files
"""
import shutil
from datetime import datetime, time
from pathlib import Path

import h5py
import pyabf
from dfply import *

from hive.convert.base import FileConverter
from hive.timer import Timer


class ABFConverter(FileConverter):

    def __init__(self, input_file,
                 output_file=None, channel_select=None, verbose=False):
        """
        Constructs a new LVMConverter
        @param input_file: the input file path
        @param output_file: the output file path
            defaults to input file with extension replaced with .h5
        @param channel_select: either a list of channel numbers or a list of adc
            names to convert
            defaults to all channels
        @param verbose: boolean governing output verbosity
        """
        if channel_select is None:
            channel_select = []

        self.__channel_select = channel_select

        # see if channel_select contains adcNames or channelNumbers
        try:
            [int(x) for x in channel_select]
        except ValueError:
            self.__use_channel_numbers = False
        else:
            self.__use_channel_numbers = True

        super().__init__(input_file, output_file, verbose, suffix='.h5')

    @property
    def channel_select(self):
        """
        The list of channels to convert
        """
        return self.__channel_select

    def process(self):
        """
        Do the conversion work
        """

        # =========================================================================
        # read data from ABF file
        # =========================================================================
        with Timer(f'read {Path(self.input_file).name}', verbose=self.verbose):
            # first, we open the file
            abf = pyabf.ABF(self.input_file)

            # next, determine the list of channels to convert
            if len(self.channel_select) == 0:
                # simple: use all channels
                channels_to_convert = abf.channelList
            elif self.__use_channel_numbers:
                # also simple: use supplied numeric list
                channels_to_convert = [int(i) for i in self.channel_select]
            else:
                # less-simple: find numeric indices in adcNames
                try:
                    channels_to_convert = [abf.adcNames.index(s) for s in self.channel_select]
                except ValueError as err:
                    if not err.args:
                        err.args = ('',)
                    err.args = err.args + (f' {abf.adcNames}',)
                    raise

            # NOTE abfload returns data in nSamples x nChannels x nSweeps

            # now, we can read in the data
            sweep_count = abf.sweepCount
            sweep_samples = abf.sweepPointCount
            sample_freq = abf.dataRate
            sweep_freq = sample_freq / sweep_samples
            sweep_times = abf.sweepTimesSec
            abf_timestamp = abf.abfDateTime.timestamp()

            #
            # required header fields for compatibility with Matlab's abfload()
            #

            # recTime: recording start and stop time in seconds from
            # midnight (millisecond resolution)
            _start_sec = (
                    abf.abfDateTime -
                    datetime.combine(
                        abf.abfDateTime.date(),
                        time(0, 0, 0))
            ).total_seconds()
            _end_sec = _start_sec + (sweep_count / sweep_freq)
            rec_time = [_start_sec, _end_sec]

            # si: sampling interval
            si = 1 / sample_freq

            # recChNames: the names of all channels, e.g. 'IN 8',...
            rec_ch_names = [abf.adcNames[i] for i in channels_to_convert]

            # sweepStartInPts: the start times of sweeps in sample points
            # (from beginning of recording)
            sweep_start_in_pts = abf.sweepTimesSec * abf.dataRate

        # =========================================================================
        # write data to H5 file
        # =========================================================================
        with Timer(f'wrote {Path(self.output_file).name}', verbose=self.verbose):
            with h5py.File(self.output_file, 'w') as f:
                with Timer(f'\twrote header', verbose=self.verbose):
                    # write the header as attributes
                    hdr = f.create_group('header')
                    hdr.attrs['sweepCount'] = sweep_count
                    hdr.attrs['sweepSampleCount'] = sweep_samples
                    hdr.attrs['sampleFreq'] = sample_freq
                    hdr.attrs['sweepFreq'] = sweep_freq
                    hdr.attrs['abfTimestamp'] = abf_timestamp
                    hdr.attrs['recTime'] = rec_time
                    hdr.attrs['si'] = si / 1e-6
                    hdr.attrs['recChNames'] = rec_ch_names

                    f.create_dataset(
                        name='header/sweepTimes',
                        data=sweep_times,
                        compression=5)

                    f.create_dataset(
                        name='header/sweepStartInPts',
                        data=sweep_start_in_pts,
                        compression=5)

                abf_data = np.zeros(shape=(
                    sweep_samples,
                    len(channels_to_convert),
                    sweep_count))

                for ix, c in enumerate(channels_to_convert):
                    abf_data[:, ix, :] = abf.data[c].reshape(
                        sweep_count,
                        sweep_samples).T

                with Timer('\twrote data', verbose=self.verbose):
                    f.create_dataset(
                        name='data',
                        data=abf_data,
                        compression=5)

            # copy permissions, times, etc. from original file
            # NOTE: must be run outside of the "with h5py.File()" block so file is closed
            shutil.copystat(self.input_file, self.output_file)
