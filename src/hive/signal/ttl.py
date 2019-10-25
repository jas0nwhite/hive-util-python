"""
Routines for ttl signal processing

Created on Oct 16, 2018

@author: jwhite
"""

from dfply import *  # @UnusedWildImport
import statistics as stats


def find_edges(input_df):
    # find the low/quiescent (most common) voltage
    v_lo = min(_modes(input_df.voltage))

    # find the most common high/active voltage
    high_df = (
            input_df >>
            mask(X.voltage > (v_lo + 1.0))
    )
    v_hi = max(_modes(high_df.voltage))

    # set threshold to 2/3
    threshold = v_lo + (v_hi - v_lo) * 2 / 3

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


def _modes(d):
    # noinspection PyProtectedMember
    table = stats._counts(d)
    modes = [table[i][0] for i in range(len(table))]
    return modes
