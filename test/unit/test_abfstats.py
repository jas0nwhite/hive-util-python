import tempfile
import unittest
from pathlib import Path

import pytest
from dfply import *  # @UnusedWildImport

from hive.report.abfstats import ABFReporter


class ReporterTest(unittest.TestCase):
    data = Path.cwd() / 'files'

    def test_file(self):
        file = str(
            self.data /
            'dataA' /
            'dataA_0001.abf'
        )
        results = ABFReporter(file) \
            .process() \
            .data_frame

        assert isinstance(results, pd.DataFrame), 'results should be a DataFrame'
        assert results.shape[0] == 2
        assert not results.isna().values.any()

    def test_flat_dir(self):
        file = str(
            self.data /
            'dataA'
        )
        results = ABFReporter(file) \
            .process() \
            .data_frame

        assert isinstance(results, pd.DataFrame), 'results should be a DataFrame'
        assert results.shape[0] == 6
        assert not results.isna().values.any()

    def test_recursive_dir(self):
        file = str(self.data)
        results = ABFReporter(
            file,
            file_pattern="dataA_*.abf",
            recurse=True) \
            .process() \
            .data_frame

        assert isinstance(results, pd.DataFrame), 'results should be a DataFrame'
        assert results.shape[0] == 6
        assert not results.isna().values.any()

    def test_nonexistent_file(self):
        file = str(self.data / "THIS_DOES_NOT_EXIST")

        with pytest.raises(FileNotFoundError):
            ABFReporter(file) \
                .process()

    def test_empty_file(self):
        file = str(self.data / "empty.abf")
        results = ABFReporter(file) \
            .process() \
            .data_frame

        assert isinstance(results, pd.DataFrame), 'results should be a DataFrame'
        assert results.shape == (0, 0)

    @staticmethod
    def test_empty_dir():
        with tempfile.TemporaryDirectory() as file:
            results = ABFReporter(file) \
                .process() \
                .data_frame

            assert isinstance(results, pd.DataFrame), 'results should be a DataFrame'
            assert results.shape == (0, 0)

    def test_TTL_IN_looks_like_second_headstage(self):
        file = str(self.data / 'dataB')
        results = ABFReporter(file) \
            .process() \
            .data_frame

        assert isinstance(results, pd.DataFrame), 'results should be a DataFrame'
        assert results.shape[0] == 3
        assert not results.isna().values.any()

    def test_structure_error(self):
        for err in ['error1.abf', 'error3.abf', 'error4.abf']:
            file = str(self.data / 'errors' / err)
            results = ABFReporter(file) \
                .process() \
                .data_frame

            assert isinstance(results, pd.DataFrame), 'results should be a DataFrame'
            assert results.shape == (0, 0)

    def test_invalid_abf_error(self):
        for err in ['error2.abf']:
            file = str(self.data / 'errors' / err)
            results = ABFReporter(file) \
                .process() \
                .data_frame

            assert isinstance(results, pd.DataFrame), 'results should be a DataFrame'
            assert results.shape == (0, 0)

    def test_calculation_error(self):
        for err in ['error5.abf']:
            file = str(self.data / 'errors' / err)
            results = ABFReporter(file) \
                .process() \
                .data_frame

            assert isinstance(results, pd.DataFrame), 'results should be a DataFrame'
            assert results.shape[0] == 1
            assert results.at[0, 'dir'] == 'errors'
            assert results.at[0, 'file'] == err
            assert not pd.isna(results.at[0, 'date'])
            assert not pd.isna(results.at[0, 'samples'])
            assert not pd.isna(results.at[0, 'sweeps'])
            assert pd.isna(results.at[0, 'sweepFreq_Hz'])
            assert not pd.isna(results.at[0, 'sampleFreq_kHz'])
            assert pd.isna(results.at[0, 'recTime_sec'])
            assert pd.isna(results.at[0, 'currentCh'])
            assert pd.isna(results.at[0, 'currentNm'])
            assert pd.isna(results.at[0, 'voltageCh'])
            assert pd.isna(results.at[0, 'voltageNm'])
            assert pd.isna(results.at[0, 'headstage'])
            assert pd.isna(results.at[0, 'forcingFn'])

    def test_error_tolerance(self):
        file = str(self.data / 'errors')
        results = ABFReporter(file) \
            .process() \
            .data_frame

        print(results)
        assert isinstance(results, pd.DataFrame), 'results should be a DataFrame'


if __name__ == '__main__':
    unittest.main()
