import sys
import types

import pytest

from volue_insight_timeseries import util

INSTALL_HINT = r"volue-insight-timeseries\[pandas\]"


@pytest.fixture
def no_pandas(monkeypatch):
    # A None entry in sys.modules makes "import pandas" raise ImportError.
    monkeypatch.setitem(sys.modules, "pandas", None)


def _fake_pandas(monkeypatch, version):
    # "import pandas" returns this module because sys.modules has it.
    fake = types.ModuleType("pandas")
    fake.__version__ = version
    monkeypatch.setitem(sys.modules, "pandas", fake)
    return fake


@pytest.mark.parametrize("version", ["1.3.5", "1.4.4", "0.25.3"])
def test_old_pandas_raises_upgrade_hint(monkeypatch, version):
    _fake_pandas(monkeypatch, version)
    with pytest.raises(ImportError, match=f"pandas {version} is installed"):
        util._require_pandas()


@pytest.mark.parametrize(
    "version", ["1.5.0", "2.2.0rc0", "3.1.0", "3.0.0.dev0+12.gabc", "unknown"]
)
def test_supported_pandas_passes(monkeypatch, version):
    fake = _fake_pandas(monkeypatch, version)
    assert util._require_pandas() is fake


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
