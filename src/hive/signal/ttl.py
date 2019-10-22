"""
Routines for ttl signal processing

Created on Oct 16, 2018

@author: jwhite
"""

from dfply import *  # @UnusedWildImport


def find_edges(input_df):

    # find the range
    v_min = input_df.voltage.min()
    v_max = input_df.voltage.max()

    # set threshold to 2/3
    threshold = v_min + (v_max - v_min) * 2 / 3

    # compute difference of signal
    signal = (
        input_df >>
        mutate(hi=1 * (X.voltage > threshold)) >>
        mutate(dHi=X.hi.diff(), dt=X.time.diff())
    )

    up = (
        signal >>
        mask(X.dHi > 0) >>
        mutate(onset=X.time - (X.dt / 2)) >>
        mutate(interval=X.onset.diff())
    ).reset_index(drop=True)

    dn = (
        signal >>
        mask(X.dHi < 0) >>
        mutate(onset=X.time - (X.dt / 2)) >>
        mutate(interval=X.onset.diff())
    ).reset_index(drop=True)

    return up, dn, threshold
