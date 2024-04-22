import pytest
import pandas as pd
from volue_insight_timeseries.util import TS, TIME_SERIES, _TS_FREQ_TABLE, _PANDAS_FREQ_TABLE

@pytest.fixture
def ts1():
    points = [[0, 80], [2678400000, 90],
              [5097600000, 70], [7776000000, 120]]
    return TS(id=1, name='This is a Name', frequency='M', time_zone='CET',
              curve_type=TIME_SERIES, points=points)


@pytest.fixture
def ts2():
    points = [[0, 120], [2678400000, 210],
              [5097600000, 330], [7776000000, 380]]
    return TS(id=2, name='This is another Name', frequency='M',
              time_zone='CET', curve_type=TIME_SERIES, points=points)


@pytest.fixture
def ts3():
    points = [[0, 220], [2678400000, 120],
              [5097600000, 140], [7776000000, 580]]
    return TS(id=3, name='This is a third Name', frequency='M',
              time_zone='CET', curve_type=TIME_SERIES, points=points)

@pytest.fixture
def ts4():
    points = [
        [2153343600000, 10],
        [2153426400000, 20],
        [2153512800000, 30]
    ]
    return TS(id=4, name='Test 2038 issue', frequency='D',
              time_zone='CET', curve_type=TIME_SERIES, points=points)

@pytest.fixture
def ts5():
    points = [[0, 220]]
    return TS(id=5, name='Test frequency', frequency='D',
              time_zone='CET', curve_type=TIME_SERIES, points=points)

def test_to_pandas_2038(ts4):
    pd_series = ts4.to_pandas()
    assert len(pd_series.index) == len(ts4.points)

def test_to_pandas(ts1, ts5):
    pd_series = ts1.to_pandas()
    assert len(pd_series.index) == len(ts1.points)

    for k, v in _TS_FREQ_TABLE.items():
        ts5.frequency = k
        pd_series_freq = ts5.to_pandas().index.freqstr
        pd_series_freq = pd_series_freq.replace('-JAN', '')
        assert pd_series_freq == v


def test_from_pandas(ts1, ts5):
    pd_series = ts1.to_pandas()
    re_ts = TS.from_pandas(pd_series)

    assert re_ts.name == ts1.name
    assert re_ts.frequency == ts1.frequency
    assert len(re_ts.points) == len(ts1.points)

    for dp1, dp2 in zip(re_ts.points, ts1.points):
        assert dp1 == dp2

    for k, v in _PANDAS_FREQ_TABLE.items():
        idx = pd.DatetimeIndex(["2024-01-01 00:00:00+02:00"], freq=k)
        pd_series_freq = pd.Series(name="test pd", index=idx, data=[220])
        re_ts5_freq = TS.from_pandas(pd_series_freq).frequency
        re_ts5_freq = re_ts5_freq.replace('-JAN', '')
        assert re_ts5_freq == v

def test_sum_ts(ts1, ts2, ts3):
    points = [[0, 420], [2678400000, 420],
              [5097600000, 540], [7776000000, 1080]]
    sum_name = 'Summed Series'
    summed = TS.sum([ts1, ts2, ts3], sum_name)

    assert summed.name == sum_name
    assert summed.frequency == ts1.frequency
    assert len(summed.points) >= len(ts1.points)
    assert len(summed.points) >= len(ts2.points)

    for dp1, dp2 in zip(points, summed.points):
        assert dp1 == dp2


def test_mean_ts(ts1, ts2, ts3):
    points = [[0, 140.0], [2678400000, 140],
              [5097600000, 180], [7776000000, 360]]
    mean_name = 'Mean Series'
    summed = TS.mean([ts1, ts2, ts3], mean_name)

    assert summed.name == mean_name
    assert summed.frequency == ts1.frequency
    assert len(summed.points) >= len(ts1.points)
    assert len(summed.points) >= len(ts2.points)

    for dp1, dp2 in zip(points, summed.points):
        assert dp1 == dp2


def test_median_ts(ts1, ts2, ts3):
    points = [[0, 120.0], [2678400000, 120],
              [5097600000, 140], [7776000000, 380]]
    median_name = 'Median Series'
    summed = TS.median([ts1, ts2, ts3], median_name)

    assert summed.name == median_name
    assert summed.frequency == ts1.frequency
    assert len(summed.points) >= len(ts1.points)
    assert len(summed.points) >= len(ts2.points)

    for dp1, dp2 in zip(points, summed.points):
        assert dp1 == dp2

def test_fullname(ts1):
    assert ts1.fullname == "This is a Name"

    ts1.name = None
    assert ts1.fullname == "1 TIME_SERIES CET M"
