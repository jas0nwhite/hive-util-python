import time
import unittest

import hive.files as hf


class TestHeaderFile(unittest.TestCase):

    def _get_test_header(self):
        hdr = hf.HeaderFile()
        hdr.fs = 1e5
        hdr.n_chans = 2
        hdr.n_samples = 1032
        hdr.n_samples_pre = 16
        hdr.n_samples_post = 16
        hdr.n_trials = 600
        hdr.label = ['FSCV_1', 'Cmd0']
        hdr.chan_type = ['adc', 'adc']
        hdr.chan_unit = ['nA', 'V']
        hdr.first_time_stamp = time.time() * 1000
        return hdr

    def test_header_to_dataframe(self):
        hdr = self._get_test_header()

        df = hdr.dataframe()

        assert df.shape == (2, 10)

        assert df.columns.tolist() == [
            'Fs',
            'chan',
            'nSamples',
            'nSamplesPre',
            'nSamplesPost',
            'nTrials',
            'label',
            'chanType',
            'chanUnit',
            'firstTimeStamp']

        assert df['Fs'].tolist() == [1e5, 1e5]
        assert df['chan'].tolist() == [0, 1]
        assert df['nSamples'].tolist() == [1032, 1032]
        assert df['nSamplesPre'].tolist() == [16, 16]
        assert df['nSamplesPost'].tolist() == [16, 16]
        assert df['label'].tolist() == ['FSCV_1', 'Cmd0']
        assert df['chanType'].tolist() == ['adc', 'adc']
        assert df['chanUnit'].tolist() == ['nA', 'V']
        assert df['firstTimeStamp'].tolist() == [hdr.first_time_stamp, hdr.first_time_stamp]


if __name__ == '__main__':
    unittest.main()
