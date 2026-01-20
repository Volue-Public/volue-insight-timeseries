.. _curves:

Access data from the API
=====================

Example
-------

The data in the API is stored in ``curves`` . A curve is a collection of metadata,
describing one or more time series.
There are 4 types of curves:

* TIME_SERIES
* TAGGED
* INSTANCES
* TAGGED_INSTANCES

Additionally, there is a specialized curve type:

* PAIRED_LIST - for data structures with two related values per point.

This chapter describes how to search for available curves in the API and
how to access the stored data, based on the given curve type.

.. _search-curves:

Searching for curves
--------------------

Each curve can have various of the following ``metadata`` attributes that
describe the curve.

* commodity
* categories
* area
* border_source
* station
* sources
* scenarios
* unit
* time_zone
* version
* frequency
* data_type


The standard way of finding curves, is by searching using a combination of these
metadata attributes. To search for curves, you can either
use the `api web interface`_ (see the `documentation`_ for more info)
or search for curves within python.

To search for curves within python, use the :meth:`volue_insight_timeseries.session.Session.search`
function.

The valid values for each attribute can be accessed using
the specific ``session.get_ATTRIBUTE`` function:

.. automethod:: volue_insight_timeseries.session.Session.search
    :noindex:


Getting a curve object
-----------------------

In order to fetch data from the API, you first have to fetch the curve you want
to read the data from. You can either do this by
:ref:`searching for curves<search-curves>` ,
since this will already return a list of curve objects. Or you can get
a curve object by its name using the :meth:`volue_insight_timeseries.session.Session.get_curve`
method::

    curve = session.get_curve(name='pro ee wnd intraday mwh/h cet h a')

Each curve has all of the following ``attributes`` :

* id: id of the curve
* name: name of the curve
* curve_state: state of the curve (`Normal availability`,
  `Beta release` or `Scheduled for removal`)
* curve_type: one of the 4 defines types (TIME_SERIES, TAGGED, INSTANCES and
  TAGGED_INSTANCES)

The value of the attribute can be accessed with ``curve.attribute_name``, eg ::

    >>> curve = session.get_curve(name='pro ee wnd intraday mwh/h cet h a')
    >>> curve.name
    pro ee wnd intraday mwh/h cet h a
    >>> curve.curve_type
    TIME_SERIES

.. automethod:: volue_insight_timeseries.session.Session.get_curve
    :noindex:


Getting data from a curve object
---------------------------------

There is a different method to get data for each of the 4 types of curves
(TIME_SERIES, TAGGED, INSTANCES, TAGGED_INSTANCES)

To find out the type of a given curve, use the ``curve.curve_type`` attribute::

    >>> curve = session.get_curve(name='pro ee wnd intraday mwh/h cet h a')
    >>> curve.curve_type # check the type of the given curve
    'TIME_SERIES'


Getting data from a TIME_SERIES curve
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A Time Series curves holds a single time series.
This is used for actual values, backcasts, normals, etc.
To get data from a Times Series curve, use the
:meth:`~volue_insight_timeseries.curves.TimeSeriesCurve.get_data` method
( :meth:`volue_insight_timeseries.curves.TimeSeriesCurve.get_data` ). You can get the data as it
is stored in the curve, by defining a start date (`data_from`) and
an end date (`data_to`) ::

    curve = session.get_curve(name='pro ee wnd intraday mwh/h cet h a')
    ts = curve.get_data(data_from='2018-01-01T14:00Z', data_to='2018-02-01T14:00Z')


.. note::
    End dates are always excluded in the result!

The :meth:`~volue_insight_timeseries.curves.TimeSeriesCurve.get_data`  method returns
a :class:`~volue_insight_timeseries.util.TS` object (:class:`volue_insight_timeseries.util.TS`).
:ref:`Here you can see how to work with an TS object<use-TS>` .

It is possible to process curves directly in the API (eg aggregating to
daily/weekly/monthly/yearly values) by using additional inputs to the
:meth:`~volue_insight_timeseries.curves.TimeSeriesCurve.get_data`
method. This can be used with great effect to reduce the amount of
data retrieved if the full set of details is not needed.
Have a look at the detailed method documentation below and at our
:ref:`examples<examples>` .


.. automethod:: volue_insight_timeseries.curves.TimeSeriesCurve.get_data
    :noindex:

Getting data from a TAGGED curve
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A tagged curve holds a set of closely related time series, each identified
by a tag. The most common use of tags is for ensemble weather data.

The existing set of tags of a curve can be found using the
:meth:`~volue_insight_timeseries.curves.TaggedCurve.get_tags` method::

    tags = curve.get_tags()

You can get data from a tagged curve using the
:meth:`~volue_insight_timeseries.curves.TaggedCurve.get_data` method. This method has the same
inputs and functionality as the :meth:`volue_insight_timeseries.curves.TimeSeriesCurve.get_data`
method for Time Series curves. Additionally you can provide a ``tag`` argument.
``tag`` can be a single value or a list of values. If omitted, the default tag
is returned. When a list of tags is requested, a list of time series is
returned::

    # get data between two dates for all tags
    ts_list = curve.get_data(data_from='2018-01-01', data_to='2018-02-01')

    # get data between two dates for single tag='Avg'
    ts = curve.get_data(data_from='2018-01-01', data_to='2018-02-01', tag='Avg')

    # get data between two dates for tags 'Avg', '01' and '12'
    ts_list = curve.get_data(data_from='2018-01-01', data_to='2018-02-01', tag=['Avg','01','12'])


.. automethod:: volue_insight_timeseries.curves.TaggedCurve.get_tags
    :noindex:

.. automethod:: volue_insight_timeseries.curves.TaggedCurve.get_data
    :noindex:



Getting data from a INSTANCES curve
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A Instance curve contains a time series for each issue_date of the curve.
This is typically a forecast with a time series for each issue_date of the
forecast.


You can fetch a single instance identified by its issue_date using the
:meth:`~volue_insight_timeseries.curves.InstanceCurve.get_instance` method::

    ts = curve.get_instance(issue_date='2018-01-01T00:00')


You can fetch multiple instances (within a given time-range) using the
:meth:`~volue_insight_timeseries.curves.InstanceCurve.search_instances` method. The function
will only return :class:`~volue_insight_timeseries.util.TS` objects with data, when the
``with_data`` argument is set to ``True`` (default is ``False`` and will return
a :class:`~volue_insight_timeseries.util.TS` object with meta data only)::

    ts_list = curve.search_instances(issue_date_from='2018-07-01Z00:00',
                                     issue_date_to='2018-07-04Z00:00',
                                     with_data=True)

You can also fetch the latest available instance using the
:meth:`~volue_insight_timeseries.curves.InstanceCurve.get_latest` method::

    ts = curve.get_latest()

.. note::
    All three methods allow to process curves directly in the API
    (eg. select date ranges, aggregating, filtering, changing timezones)
    by using additional inputs. Have a look at the detailed function
    descriptions below and at the provided :ref:`examples<examples>`.

.. automethod:: volue_insight_timeseries.curves.InstanceCurve.get_instance
    :noindex:

.. automethod:: volue_insight_timeseries.curves.InstanceCurve.search_instances
    :noindex:

.. automethod:: volue_insight_timeseries.curves.InstanceCurve.get_latest
    :noindex:


Getting data from a TAGGED_INSTANCES curve
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Tagged Instance curves are a combination of Tagged curves and Instance curves.
A Tagged Instance curve typically represents forecasts that contain
multiple time series for each issue_date of the forecast, which are
assigned to tags. Each time series is therefore defined by a
unique combination of issue_date and tag. Ensamble forecasts are a
typical use case for Tagged Instance curves.

The existing set of tags of a curve can be found using the
:meth:`~volue_insight_timeseries.curves.TaggedInstanceCurve.get_tags` method::

    tags = curve.get_tags()

You can fetch a single instance identified by its issue_date using the
:meth:`~volue_insight_timeseries.curves.InstanceCurve.get_instance` method.
This function allows you the specify a single tag or a list of tags to the
``tag`` argument. If omitted, the default tag is returned. ::

    # get data for this issue date for the default tag of the curve ('Avg')
    ts_list = curve.get_instance(issue_date='2018-07-01T00:00')

    # get data for this issue date for single tag='Avg'
    ts = curve.get_instance(issue_date='2018-07-01T00:00', tag='Avg')

     # get data for this issue date for tags 'Avg', '02' and '05'
    ts_list = curve.get_instance(issue_date='2018-07-01T00:00', tag=['Avg','02','05'])

You can fetch multiple instances (within a given time-range) using the
:meth:`~volue_insight_timeseries.curves.TaggedInstanceCurve.search_instances` method. The function
will only return :class:`~volue_insight_timeseries.util.TS` objects with data, when the ``with_data``
argument is set to ``True`` (default is ``False`` and will return a
:class:`~volue_insight_timeseries.util.TS` object with meta data only). Here you can again omit
the ``tags`` argument, which returns the default tag for each
issue_date, or specify a single tag or a list of tags. ::

    ts_list = curve.search_instances(issue_date_from='2018-07-01Z00:00',
                                     issue_date_to='2018-07-04Z00:00',
                                     with_data=True,
                                     tags=['Avg','11'])

You can also fetch the latest available instance using the
:meth:`~volue_insight_timeseries.curves.InstanceCurve.get_latest` method. This function will always
return exactly ONE Time Series curve for ONE tag of the latest issue_date.
It is possible to provide a list of tags to the ``tags`` argument,
but it is strongly recommended to specify ONE SINGLE TAG here! If omitted,
the default tag is returned. ::

    ts = curve.get_latest(tags='03')

.. note::
    All three methods to get data allow to process curves directly in the API
    (eg. select date ranges, aggregating, filtering, changing timezones)
    by using additional inputs. Have a look at the detailed function
    descriptions below and at the provided :ref:`examples<examples>`.

.. automethod:: volue_insight_timeseries.curves.TaggedInstanceCurve.get_tags
    :noindex:

.. automethod:: volue_insight_timeseries.curves.TaggedInstanceCurve.get_instance
    :noindex:

.. automethod:: volue_insight_timeseries.curves.TaggedInstanceCurve.search_instances
    :noindex:

.. automethod:: volue_insight_timeseries.curves.TaggedInstanceCurve.get_latest
    :noindex:

Getting data from a PAIRED_LIST curve
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A PairedList curve contains paired values where each data point has two related values, such
as price and volume.

The existing set of tags of a curve can be found using the
:meth:`~volue_insight_timeseries.curves.PairedListCurve.get_tags` method::

        tags = curve.get_tags()

You can fetch paired data using the
:meth:`~volue_insight_timeseries.curves.PairedListCurve.get_data` method.
The ``with_data`` argument controls whether to return full data (``True``) or metadata only (``False``)::


      paired_data = curve.get_data(data_from='2025-01-01',
                                    data_to='2025-01-31',
                                    with_data=True)

When ``with_data=True``, the method returns :class:`~volue_insight_timeseries.util.PairedTS` objects
which contain the paired values. These can be converted to a pandas DataFrame where each tag becomes a column::

      # convert to DataFrame
      df = paired_data[0].to_pandas()

  .. note::
      PairedList curves do not support the following methods: ``get_latest()``,
      ``get_instance()``, ``search_instances()``, ``get_relative()``, and ``get_absolute()``.
      These methods will raise a ``MethodNotApplicable`` exception.

  .. automethod:: volue_insight_timeseries.curves.PairedListCurve.get_tags
      :noindex:

  .. automethod:: volue_insight_timeseries.curves.PairedListCurve.get_data
      :noindex:

.. _use-TS:

Working with data from a curve object
--------------------------------------

Independent from the curve type and the respective method to get the data,
all these methods return a :class:`~volue_insight_timeseries.util.TS` object
(:class:`volue_insight_timeseries.util.TS`).

The most important function of the :class:`~volue_insight_timeseries.util.TS` class, is the
:meth:`~volue_insight_timeseries.util.TS.to_pandas` function,
which will return a `pandas.Series`_ object with a date index, containing the
data of the curve::

    >>> curve = session.get_curve(name='pro ee wnd intraday mwh/h cet h a')
    >>> ts = curve.get_data(data_from="2018-01-01", data_to="2018-01-05",
    >>>                     frequency="D", function="SUM")
    >>> ts.to_pandas()
    2018-01-01 00:00:00+01:00    2169.0
    2018-01-02 00:00:00+01:00    3948.0
    2018-01-03 00:00:00+01:00    1489.0
    2018-01-04 00:00:00+01:00    1860.0
    Freq: D, Name: pro ee wnd intraday mwh/h cet h a, dtype: float64

Have a look at our :ref:`examples<examples>` or at
the `pandas documentation`_ , to see how to work
with `pandas.Series`_ or `pandas.DataFrame`_ objects.

.. automethod:: volue_insight_timeseries.util.TS.to_pandas
    :noindex:


The :class:`~volue_insight_timeseries.util.TS` class contains some simple aggregation functions, which can be
used directly on a :class:`~volue_insight_timeseries.util.TS` object:
:meth:`~volue_insight_timeseries.util.TS.sum` , :meth:`~volue_insight_timeseries.util.TS.mean`
and :meth:`~volue_insight_timeseries.util.TS.median` .

.. automethod:: volue_insight_timeseries.util.TS.sum
    :noindex:

.. automethod:: volue_insight_timeseries.util.TS.mean
    :noindex:

.. automethod:: volue_insight_timeseries.util.TS.median
    :noindex:


PAIRED_LIST curves return :class:`~volue_insight_timeseries.util.PairedTS` objects
instead of regular :class:`~volue_insight_timeseries.util.TS` objects.
The :meth:`~volue_insight_timeseries.util.PairedTS.to_pandas` function
returns a `pandas.DataFrame`_ object (instead of a Series) where each tag becomes a column::

  >>> curve = session.get_curve(name='paired_list curve name')
  >>> paired_data = curve.get_data(data_from="2025-12-18", data_to="2025-12-19", with_data=True)
  >>> df = paired_data[0].to_pandas()
  >>> df.head()
       price  volume
  0  -581.93     5.0
  1  -572.00     5.0
  2  -562.97     5.0
  3  -544.84     5.0
  4  -536.21     5.0

.. automethod:: volue_insight_timeseries.util.PairedTS.to_pandas
  :noindex:

.. _api web interface: https://api.volueinsight.com/
.. _documentation: https://api.volueinsight.com/#documentation
.. _pandas.Series: https://pandas.pydata.org/pandas-docs/stable/generated/pandas.Series.html
.. _pandas.DataFrame: https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.html
.. _pandas documentation: https://pandas.pydata.org/pandas-docs/stable/index.html
