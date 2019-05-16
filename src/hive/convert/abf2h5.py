'''
Created on May 15, 2019

@author: jwhite

Converter for voltammetry ABF (Axon binary format) files
'''
from pathlib import Path

from dfply import *  # @UnusedWildImport
import pyabf
import h5py

from hive.convert.base import FileConverter
from hive.timer import Timer


class ABFConverter(FileConverter):

    def __init__(self, input_file, output_file=None, channel_select=[], verbose=False):
        """
        Constructs a new LVMConverter
        @param input_file: the input file path
        @param output_file: the output file path
            defaults to input file with extension replaced with .h5
        @param channel_select: either a list of channel numbers or a list of adc names to convert
            defaults to all channels
        @param verbose: boolean governing output verbosity
        """
        self.__channel_select = channel_select

        # see if channel_select contains adcNames or channelNumbers
        try:
            [int(x) for x in self.channel_select]
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

        #=========================================================================
        # read data from ABF file
        #=========================================================================
        with Timer(f'read {Path(self.input_file).name}', verbose=self.verbose):
            # first, we open the file
            abf = pyabf.ABF(self.input_file)

            # next, determine the list of channels to convert
            if len(self.channel_select) == 0:
                # simple: use all channels
                channels_to_convert = abf.channelList
            elif self.__use_channel_numbers:
                # also simple: use supplied numeric list
                channels_to_convert = self.channel_select
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

        #=========================================================================
        # write data to H5 file
        #=========================================================================
        with Timer(f'wrote {Path(self.output_file).name}', verbose=self.verbose):
            with h5py.File(self.output_file, 'w') as f:
                with Timer(f'\twrote header', verbose=self.verbose):
                    # write the header as attributes
                    hdr = f.create_group('header')
                    hdr.attrs['sweepCount'] = sweep_count
                    hdr.attrs['sweepSampleCount'] = sweep_samples
                    hdr.attrs['sampleFreq'] = sample_freq
                    hdr.attrs['sweepFreq'] = sweep_freq

                    f.create_dataset('sweepTimes', data=sweep_times, compression=5)

                    data_grp = f.create_group('data')

                # ...and a table for each channel
                for chan in channels_to_convert:
                    ch_data = abf.data[chan].reshape(sweep_count, sweep_samples).T
                    ch_name = abf.adcNames[chan]

                    with Timer(f'\twrote {ch_name}', verbose=self.verbose):
                        data_grp.create_dataset(ch_name, data=ch_data, compression=5)
