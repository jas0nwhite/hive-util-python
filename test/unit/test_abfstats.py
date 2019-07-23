import unittest

from hive.report.abfstats import ABFReporter
from pathlib import Path

from dfply import *  # @UnusedWildImport

import pytest


class ReporterTest(unittest.TestCase):
    home = Path('/Volumes/external/hnl/in-vitro/incoming/.earth/Data')

    def test_file(self):
        file = str(
            self.home / '2019_07_09_DA_NE_pH76_XXX_MMP001_2ch' / '2019_07_09_DA_NE_pH76_XXX_MMP001_2ch_0000.abf')
        results = ABFReporter(file) \
            .process() \
            .dataFrame

        assert isinstance(results, pd.DataFrame), "file list should be a list"
        assert results.shape[0] == 1 * 2

    def test_flat_dir(self):
        file = str(self.home / '2019_05_23_rodentB_triangle_01_CFR003')
        results = ABFReporter(file) \
            .process() \
            .dataFrame

        assert isinstance(results, pd.DataFrame), "file list should be a list"
        assert results.shape[0] == 5 * 1

    def test_recursive_dir(self):
        file = str(self.home)
        results = ABFReporter(file, file_pattern="2019_07_01_chara*.abf", recurse=True) \
            .process() \
            .dataFrame

        assert isinstance(results, pd.DataFrame), "file list should be a list"
        assert results.shape[0] == 6 * 2

    def test_nonexistant_file(self):
        file = str(self.home / "THIS_DOES_NOT_EXIST")

        with pytest.raises(FileNotFoundError):
            ABFReporter(file) \
                .process()

    def test_TTL_IN_looks_like_second_headstage(self):
        file = str(self.home / '2018_12_05_PT004')
        results = ABFReporter(file) \
            .process() \
            .dataFrame

        assert isinstance(results, pd.DataFrame), "file list should be a list"
        assert results.shape[0] == 9 * 2

    def test_for_all(self):
        file = self.home

        results = ABFReporter(file, file_pattern="**/20*.abf") \
            .process() \
            .dataFrame

        results.to_csv(self.home / "census.csv", float_format='%0.1f', index=False)


if __name__ == '__main__':
    unittest.main()
