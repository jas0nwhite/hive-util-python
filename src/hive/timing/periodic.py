'''
Created on Oct 11, 2018

@author: jwhite
'''

from dfply import *  # @UnusedWildImport


class PeriodicSignal(object):
    '''
    classdocs
    '''

    def __init__(self, onsets):
        '''
        Constructor
        :param pd.Series onsets: time series of event onsets
        '''
        self._onset_times = onsets              #: :type _onset_times: pd.Series
        self._added_times = pd.Series([])       #: :type _added_times: pd.Series
        self._removed_times = pd.Series([])     #: :type _removed_times: pd.Series
        self._estimated_period = np.nan         #: :type _estimated_period: float
        self._mean_period = np.nan              #: :type _mean_period: float
        self._start_time = np.nan               #: :type _start_time: float
        self._end_time = np.nan                 #: :type _end_time: float
        self._target_count = -1                 #: :type _target_count: int
        self._hit_count = -1                    #: :type _hit_count: int
        self._miss_count = -1                   #: :type _miss_count: int
        self._false_count = -1                  #: :type _false_count: int

        self._characterize()

    @property
    def onset_times(self):
        return self._onset_times

    @property
    def added_times(self):
        return self._added_times

    @property
    def removed_times(self):
        return self._removed_times

    @property
    def estimated_period(self):
        return self._estimated_period

    @property
    def mean_period(self):
        return self._mean_period

    @property
    def start_time(self):
        return self._start_time

    @property
    def end_time(self):
        return self._end_time

    @property
    def target_count(self):
        return self._target_count

    @property
    def hit_count(self):
        return self._hit_count

    @property
    def miss_count(self):
        return self._miss_count

    @property
    def false_count(self):
        return self._false_count

    def __str__(self):
        '''
        str() method
        :rtype str
        '''
        return (
            '''    start: %14.9f
    end:   %14.9f
    ePer:  %14.9f
    mPer:  %14.9f
    count: %4d
    hits:  %4d
    skips: %4d
    extra: %4d'''
        ) % (
            self._start_time, self._end_time, self._estimated_period, self._mean_period,
            self._target_count, self._hit_count, self._miss_count, self._false_count
        )

    def _characterize(self):
        '''
        Calculate various characteristics of the periodic signal
        :param float expected_period: expected period of signal
        '''
        self._start_time = self._onset_times.iloc[0]
        self._end_time = self._onset_times.iloc[-1]

        periods = self._onset_times.sort_values().diff()  #: :type periods: pd.Series

        self._estimated_period = periods.mode().max()

        period_min = 0.5 * self._estimated_period
        period_max = 1.5 * self._estimated_period

        self._mean_period = periods[
            (periods <= period_max) & (periods > period_min)
        ].mean(skipna=True)

        self._false_count = periods[
            periods <= period_min
        ].size

        self._hit_count = self._onset_times.size - self._false_count

        self._target_count = (
            (self._end_time - self._start_time) / self._mean_period
        ).round(decimals=0) + 1

        self._miss_count = self._target_count - self._hit_count

        return None

    def regularize(self, target_period, tolerance):
        '''
        add/remove onset times to make this PeriodicSignal regular
        :param target_period float: period (in seconds)
        :param tolerance float: tolerance (percentage)
        :rtype PeriodicSignal
        '''
        times, added_times, removed_times = self._condition_timeline(
            target_period, tolerance)

        regularized = PeriodicSignal(times)
        regularized._added_times = added_times
        regularized._removed_times = removed_times

        return regularized

    def _condition_timeline(self, target_period, tolerance):
        '''
        add events that are missing
        (ported from matlab)
        :param target_period float: period (in seconds)
        :param tolerance float: tolerance (percentage)
        :rtype pd.Series
        '''
        def matlab_fn(input_times, target_period, tolerance, calc_missing_time):
            t_last = 0
            out = []
            added = []
            removed = []

            for _, t in enumerate(input_times):
                if (t_last == 0):
                    out.append(t)
                else:
                    gap = (t - t_last)

                    if (gap <= (1 - tolerance) * target_period):
                        # spurious event ==> skip
                        removed.append(t)
                        continue
                    elif (gap > (1 + tolerance) * target_period):
                        # missed event(s) ==> insert event
                        t0 = t_last

                        # use ideal (target) period to estimate number of missing
                        # events, but use linear approximation for period between
                        # synthesized events
                        est_synth_count = round(gap / target_period)
                        est_synth_period = gap / est_synth_count
                        gap_remaining = gap

                        while (gap_remaining > (1 + tolerance) * target_period):
                            t1 = calc_missing_time(t0, est_synth_period)
                            out.append(t1)
                            added.append(t1)
                            gap_remaining = gap_remaining - target_period
                            t0 = t1

                    out.append(t)

                t_last = t

            return out, added, removed

        input_times = self._onset_times.values

        def calc_missing_time(t, _):
            # this version uses the target_period rather than linear approximation
            return t + target_period

        out, added, removed = matlab_fn(input_times, target_period,
                                        tolerance, calc_missing_time)

        return pd.Series(out), pd.Series(added), pd.Series(removed)

    def _remove_extra_events(self, target_period, tolerance):
        '''
        remove extra/spurious events
        :param target_period float: period (in seconds)
        :param tolerance float: tolerance (percentage)
        :rtype pd.Series
        '''
        input_times = self._onset_times.values
        t_last = 0
        del_ix = []

        for i, t in enumerate(input_times):
            gap = (t - t_last)

            if (gap <= (1 - tolerance) * target_period):
                # spurious event ==> remove
                del_ix.append(i)
                continue

            t_last = t

        return self._onset_times.iloc(del_ix)


class Alignment(object):
    '''
    classdocs
    '''

    def __init__(self, digital, behavior):
        '''
        constructor
        :param pd.Series a:
        :param pd.Series b:
        '''
        self._digital = digital
        self._behavior = behavior
