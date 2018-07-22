#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 20 15:25:35 2018

@author: jwhite
"""

from dfply import *  # @UnusedWildImport


class HeaderFile(object):

    def __init__(self):
        self._fs = float('nan')
        self._n_chans = 0
        self._n_samples = 0
        self._n_samples_pre = 0
        self._n_samples_post = 0
        self._n_trials = 0
        self._label = []
        self._chan_type = []
        self._chan_unit = []
        self._first_time_stamp = float('nan')

    @property
    def fs(self):
        return self._fs

    @fs.setter
    def fs(self, value):
        self._fs = float(value)

    @property
    def n_chans(self):
        return self._n_chans

    @n_chans.setter
    def n_chans(self, value):
        self._n_chans = int(value)

    @property
    def n_samples(self):
        return self._n_samples

    @n_samples.setter
    def n_samples(self, value):
        self._n_samples = int(value)

    @property
    def n_samples_pre(self):
        return self._n_samples_pre

    @n_samples_pre.setter
    def n_samples_pre(self, value):
        self._n_samples_pre = int(value)

    @property
    def n_samples_post(self):
        return self._n_samples_post

    @n_samples_post.setter
    def n_samples_post(self, value):
        self._n_samples_post = int(value)

    @property
    def n_trials(self):
        return self._n_trials

    @n_trials.setter
    def n_trials(self, value):
        self._n_trials = int(value)

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, values):
        self._label = list(values)

    @property
    def chan_type(self):
        return self._chan_type

    @chan_type.setter
    def chan_type(self, values):
        self._chan_type = list(values)

    @property
    def chan_unit(self):
        return self._chan_unit

    @chan_unit.setter
    def chan_unit(self, values):
        self._chan_unit = list(values)

    @property
    def first_time_stamp(self):
        return self._first_time_stamp

    @first_time_stamp.setter
    def first_time_stamp(self, value):
        self._first_time_stamp = float(value)

    def as_dict(self, index):
        return {
            'Fs': self.fs,
            'chan': index,
            'nSamples': self.n_samples,
            'nSamplesPre': self.n_samples_pre,
            'nSamplesPost': self.n_samples_post,
            'nTrials': self.n_trials,
            'label': self.label[index],
            'chanType': self.chan_type[index],
            'chanUnit': self.chan_unit[index],
            'firstTimeStamp': self.first_time_stamp
        }

    def dataframe(self):
        return (pd.DataFrame([self.as_dict(i) for i in range(self.n_chans)]) >>
                select(X.Fs, X.chan, X.nSamples, X.nSamplesPre, X.nSamplesPost,
                       X.nTrials, X.label, X.chanType, X.chanUnit,
                       X.firstTimeStamp)
                )
