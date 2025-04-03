import pytest
import pandas as pd
from datetime import datetime
from unittest import mock
from volue_insight_timeseries.util import TS, TIME_SERIES


@pytest.fixture
def ts1():
    points = [[0, 80], [2678400000, 90], [5097600000, 70], [7776000000, 120]]
    return TS(id=1, name="This is a Name", frequency="M", time_zone="CET", curve_type=TIME_SERIES, points=points)


@pytest.fixture
def ts2():
    points = [[0, 120], [2678400000, 210], [5097600000, 330], [7776000000, 380]]
    return TS(id=2, name="This is another Name", frequency="M", time_zone="CET", curve_type=TIME_SERIES, points=points)


@pytest.fixture
def ts3():
    points = [[0, 220], [2678400000, 120], [5097600000, 140], [7776000000, 580]]
    return TS(id=3, name="This is a third Name", frequency="M", time_zone="CET", curve_type=TIME_SERIES, points=points)


@pytest.fixture
def ts4():
    points = [[2153343600000, 10], [2153426400000, 20], [2153512800000, 30]]
    return TS(id=4, name="Test 2038 issue", frequency="D", time_zone="CET", curve_type=TIME_SERIES, points=points)


@pytest.fixture
def ts5():
    points = [[0, 220]]
    return TS(id=5, name="Test frequency", frequency="D", time_zone="CET", curve_type=TIME_SERIES, points=points)


@pytest.fixture
def ts6():
    points = [
        [int(datetime.fromisoformat("2025-04-01T07:00:00").timestamp() * 1000), 106],
        [int(datetime.fromisoformat("2025-04-02T06:00:00").timestamp() * 1000), 206],
        [int(datetime.fromisoformat("2025-04-03T06:00:00").timestamp() * 1000), 306],
        [int(datetime.fromisoformat("2025-04-04T06:00:00").timestamp() * 1000), 406],
        [int(datetime.fromisoformat("2025-04-05T07:00:00").timestamp() * 1000), 506],
    ]
    return TS(id=6, name="Test irregular frequency", frequency="D", time_zone="CET", curve_type=TIME_SERIES, points=points)


@pytest.fixture
def ts7():
    points = [
        [int(datetime.fromisoformat("2025-04-01T06:00:00").timestamp() * 1000), 106],
        [int(datetime.fromisoformat("2025-04-02T06:00:00").timestamp() * 1000), 206],
        [int(datetime.fromisoformat("2025-04-03T06:00:00").timestamp() * 1000), 306],
        [int(datetime.fromisoformat("2025-04-04T06:00:00").timestamp() * 1000), 406],
        [int(datetime.fromisoformat("2025-04-05T06:00:00").timestamp() * 1000), 506],
    ]
    return TS(id=7, name="Test regular frequency", frequency="D", time_zone="CET", curve_type=TIME_SERIES, points=points)


def test_to_pandas_2038(ts4):
    pd_series = ts4.to_pandas()
    assert len(pd_series.index) == len(ts4.points)


def test_to_pandas(ts1):
    pd_series = ts1.to_pandas()
    assert len(pd_series.index) == len(ts1.points)


def test_to_pandas_freq_table_compatibility(ts5):
    # Frequency mapping from TS to all supported versions of Pandas
    ts2pd_freq = {
        "Y": ["YS-JAN", "AS-JAN"],
        "S": ["2QS-JAN"],
        "Q": ["QS-JAN"],
        "M": ["MS"],
        "W": ["W-MON"],
        "H12": ["12h", "12H"],
        "H6": ["6h", "6H"],
        "H3": ["3h", "3H"],
	"H": ["h", "H"],
        "MIN30": ["30min", "30T"],
        "MIN15": ["15min", "15T"],
        "MIN5": ["5min", "5T"],
        "MIN": ["min", "T"],
    }

    for ts_original_freq, pandas_original_freq in ts2pd_freq.items():
        ts5.frequency = ts_original_freq
        pd_series_freq = ts5.to_pandas().index.freqstr
        assert pd_series_freq in pandas_original_freq


def test_from_pandas(ts1):
    pd_series = ts1.to_pandas()
    re_ts = TS.from_pandas(pd_series)

    assert re_ts.name == ts1.name
    assert re_ts.frequency == ts1.frequency
    assert len(re_ts.points) == len(ts1.points)

    for dp1, dp2 in zip(re_ts.points, ts1.points):
        assert dp1 == dp2


def test_from_pandas_freq_table_compatibility(ts5):
    # Frequency mapping from current version of Pandas
    # NOTE: older version of Pandas (1.5.2) accepts
    # new freq name vales but outputs old freq name values
    # so it's enough to use the new freq names
    pd2ts_freq = {
        "YS": "Y",
        "2QS": "S",
        "QS": "Q",
        "MS": "M",
        "W-MON": "W",
        "12h": "H12",
        "6h": "H6",
        "3h": "H3",
	"h": "H",
        "30min": "MIN30",
        "15min": "MIN15",
        "5min": "MIN5",
        "min": "MIN",
    }

    for pandas_original_freq, ts_original_freq in pd2ts_freq.items():
        idx = pd.DatetimeIndex(["2024-01-01 00:00:00+02:00"], freq=pandas_original_freq)
        pd_series_freq = pd.Series(name="test pd", index=idx, data=[220])
        re_ts5_freq = TS.from_pandas(pd_series_freq).frequency
        assert re_ts5_freq == ts_original_freq


def test_from_pandas_irregular_frequency_warning(ts6):
    # Expect a warning when converting TS to pandas with irregular frequency
    with pytest.warns(
        RuntimeWarning,
        match="Data length mismatch: original data length is 5, but mapped frequency data length is 2. This may indicate data truncation.",
    ):
        _ = ts6.to_pandas()


def test_from_pandas_regular_frequency_no_warning(ts7):
    # Expect no warning when converting TS to pandas with regular frequency
    with mock.patch("warnings.warn") as mock_warn:
        _ = ts7.to_pandas()

    mock_warn.assert_not_called()


def test_sum_ts(ts1, ts2, ts3):
    points = [[0, 420], [2678400000, 420], [5097600000, 540], [7776000000, 1080]]
    sum_name = "Summed Series"
    summed = TS.sum([ts1, ts2, ts3], sum_name)

    assert summed.name == sum_name
    assert summed.frequency == ts1.frequency
    assert len(summed.points) >= len(ts1.points)
    assert len(summed.points) >= len(ts2.points)

    for dp1, dp2 in zip(points, summed.points):
        assert dp1 == dp2


def test_mean_ts(ts1, ts2, ts3):
    points = [[0, 140.0], [2678400000, 140], [5097600000, 180], [7776000000, 360]]
    mean_name = "Mean Series"
    summed = TS.mean([ts1, ts2, ts3], mean_name)

    assert summed.name == mean_name
    assert summed.frequency == ts1.frequency
    assert len(summed.points) >= len(ts1.points)
    assert len(summed.points) >= len(ts2.points)

    for dp1, dp2 in zip(points, summed.points):
        assert dp1 == dp2


def test_median_ts(ts1, ts2, ts3):
    points = [[0, 120.0], [2678400000, 120], [5097600000, 140], [7776000000, 380]]
    median_name = "Median Series"
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
