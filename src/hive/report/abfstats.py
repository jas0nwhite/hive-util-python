"""
Created on July 22, 2019

@author: jwhite

Reporting utility for voltammetry ABF (Axon binary format) files
"""

import os
from datetime import datetime, time
from pathlib import Path
from typing import List

import pyabf
from dfply import *  # @UnusedWildImport


class ABFReporter:
    __epoch_type = {
        0: 'disabled',
        1: 'stepped',
        2: 'ramp',
        3: 'rect. pulse train',
        4: 'triangle',
        5: 'cosine',
        6: 'ABF_EPOCH_TYPE_RESISTANCE',
        7: 'biphasic pulse train',
        8: 'IonWorks-style ramp waveform'
    }

    def __init__(self, input_path='.', file_pattern='*.abf', recurse=False):
        self.__inputPath = Path(input_path)
        self.__filePattern = file_pattern
        self.__recurse = recurse
        self.__inputFileList = []
        self.__abfHeaderList: List[pyabf.ABF] = []
        self.__dataFrame = pd.DataFrame()

    @property
    def input_path(self):
        return self.__inputPath

    @property
    def recurse(self):
        return self.__recurse

    @property
    def file_pattern(self):
        return self.__filePattern

    @property
    def input_file_list(self):
        return self.__inputFileList

    @property
    def abf_header_list(self):
        return self.__abfHeaderList

    @property
    def data_frame(self):
        return self.__dataFrame

    def __build_file_list(self):
        input_path = self.input_path.resolve()

        if not input_path.exists():
            raise FileNotFoundError(input_path)

        if input_path.is_dir():
            if self.recurse:
                file_list = sorted(
                    list(input_path.glob('**/' + self.file_pattern)),
                    key=lambda f: os.path.getmtime(f))
            else:
                file_list = sorted(
                    list(input_path.glob(self.file_pattern)),
                    key=lambda f: os.path.getmtime(f))
        else:
            file_list = [self.input_path]

        self.__inputFileList = file_list

    def __read_abf_headers(self):
        abf_header_list = [
            self.__read_abf(file, False)
            for file in self.input_file_list
        ]

        self.__abfHeaderList = abf_header_list

    @staticmethod
    def __read_abf(file, load_data=False):
        try:
            abf = pyabf.ABF(str(file), loadData=load_data)
        except Exception as e:
            print(f'*** {repr(e)} while reading {file}')
            abf = None

        return abf

    def __make_row(self, abf: pyabf.ABF, ch: int):
        # dir/file
        abf_path = Path(abf.abfFilePath.replace('\\', '/'))

        try:
            # noinspection PyProtectedMember
            adc_ch = abf._adcSection.nADCNum[ch]

            sweep_count = abf.sweepCount
            sweep_samples = abf.sweepPointCount
            sample_freq = abf.dataRate
            sweep_freq = sample_freq / sweep_samples

            # recTime: recording start and stop time in seconds from
            # midnight (millisecond resolution)
            _start_sec = (
                    abf.abfDateTime -
                    datetime.combine(
                        abf.abfDateTime.date(),
                        time(0, 0, 0))
            ).total_seconds()
            _end_sec = _start_sec + (sweep_count / sweep_freq)

            # protocol
            protocol_path = Path(abf.protocolPath.replace('\\', '/'))

            # voltageCh
            if adc_ch + 1 < len(abf.adcNames):
                voltage_ch = int(adc_ch + 1)
                voltage_name = abf.adcNames[voltage_ch]
            else:
                voltage_ch = -1
                voltage_name = ''

            dac_ch = int(ch / 2)
            # noinspection PyProtectedMember
            wave_src = abf._dacSection.nWaveformSource[dac_ch]

            if wave_src == 2:  # ABF_DACFILEWAVEFORM
                # noinspection PyProtectedMember
                forcing_fn = Path(abf._stringsIndexed.lDACFilePath[dac_ch].replace('\\', '/')).name
            elif wave_src == 1:  # ABF_EPOCHTABLEWAVEFORM
                #
                # TODO: investigate possible bug?
                #
                # noinspection PyProtectedMember
                epoch_types = abf._epochPerDacSection.nEpochType

                if len(epoch_types) == 0:
                    forcing_fn = f''
                else:
                    epd_ch = min(dac_ch, len(epoch_types) - 1)
                    epoch_type = epoch_types[epd_ch]
                    forcing_fn = self.__epoch_type[epoch_type]
            else:
                forcing_fn = f'unknown: {wave_src}'

            return {
                "dir": abf_path.parent.name,
                "file": abf_path.name,
                "date": abf.abfDateTime,
                "protocol": protocol_path.name,
                "samples": abf.sweepPointCount,
                "sweeps": abf.sweepCount,
                "sweepFreq_Hz": sweep_freq,
                "sampleFreq_kHz": abf.dataRate / 1e3,
                "recTime_sec": _end_sec - _start_sec,
                "currentCh": adc_ch,
                "currentNm": abf.adcNames[ch],
                "voltageCh": voltage_ch,
                "voltageNm": voltage_name,
                "headstage": int(adc_ch / 2) + 1,
                "forcingFn": forcing_fn
            }
        except Exception as e:
            print(f'*** {repr(e)} while reading {abf_path}')
            return {
                "dir": abf_path.parent.name,
                "file": abf_path.name,
                "date": abf.abfDateTime,
                "protocol": repr(e),
                "samples": abf.sweepPointCount,
                "sweeps": abf.sweepCount,
                "sweepFreq_Hz": pd.NA,
                "sampleFreq_kHz": abf.dataRate / 1e3,
                "recTime_sec": pd.NA,
                "currentCh": pd.NA,
                "currentNm": pd.NA,
                "voltageCh": pd.NA,
                "voltageNm": pd.NA,
                "headstage": pd.NA,
                "forcingFn": pd.NA
            }

    def __make_row_list(self):
        self.__row_list = [
            self.__make_row(abf, ch)
            for abf in self.__abfHeaderList if abf
            for ch in abf.channelList if ch % 2 == 0 and "fscv" in abf.adcNames[ch].lower()
        ]

    def process(self):

        self.__build_file_list()
        self.__read_abf_headers()
        self.__make_row_list()

        if len(self.__row_list) == 0:
            df = pd.DataFrame()
        else:
            df = (
                    pd.DataFrame(self.__row_list) >>
                    select(
                        X.dir,
                        X.file,
                        X.date,
                        X.protocol,
                        X.samples,
                        X.sweeps,
                        X.sweepFreq_Hz,
                        X.sampleFreq_kHz,
                        X.recTime_sec,
                        X.currentCh,
                        X.currentNm,
                        X.voltageCh,
                        X.voltageNm,
                        X.headstage,
                        X.forcingFn) >>
                    arrange(X.date, X.headstage)
            )

        self.__dataFrame = df

        return self
