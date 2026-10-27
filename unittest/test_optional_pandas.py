import sys

import pytest

from volue_insight_timeseries import util

INSTALL_HINT = r"volue-insight-timeseries\[pandas\]"


@pytest.fixture
def no_pandas(monkeypatch):
    # A None entry in sys.modules makes "import pandas" raise ImportError.
    monkeypatch.setitem(sys.modules, "pandas", None)


def _ts():
    return util.TS(name="curve", frequency="H", points=[[0, 1.0]])


def test_core_ts_works_without_pandas(no_pandas):
    assert _ts().fullname == "curve"


def test_to_pandas_raises_install_hint(no_pandas):
    with pytest.raises(ImportError, match=INSTALL_HINT):
        _ts().to_pandas()


def test_from_pandas_raises_install_hint(no_pandas):
    with pytest.raises(ImportError, match=INSTALL_HINT):
        util.TS.from_pandas(None)


def test_aggregation_raises_install_hint(no_pandas):
    with pytest.raises(ImportError, match=INSTALL_HINT):
        util.TS.sum([_ts()], "total")


def test_tags_to_df_raises_install_hint(no_pandas):
    with pytest.raises(ImportError, match=INSTALL_HINT):
        util.tags_to_DF([_ts()])


def test_paired_to_pandas_raises_install_hint(no_pandas):
    paired = util.PairedTS(
        input_dict={
            "name": "paired",
            "frequency": "H",
            "tags": ["a"],
            "points": [],
        }
    )
    with pytest.raises(ImportError, match=INSTALL_HINT):
        paired.to_pandas()
