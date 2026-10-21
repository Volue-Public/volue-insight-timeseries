"""
Lead time analysis for residual load, wind production, spv production and consumption:

The user decides what forecast to use as benchmark forecast and what intraday forecast to use.
The user also defines what issue date to look at from the benchmark forecast, the timestamp of interest (data time) and
the time delta (how far back to look).
This code then subtracts the estimated residual load, wind production, spv production and consumption from the benchmark
forecast with the intraday forecast. This way we can investigate how the intraday forecast differs from the
benchmark forecast for each release (each 15 min).


Used libraries:
volue_insight_timeseries: A library from volue used to access the Volue Data & Forecasts API. To install, run: pip install
volue-insight-timeseries.
pandas:                   A python library used to handle data. To install, run pip install pandas
os:                       Functionalities for interacting with the operating system. This is a standard python library,
                          so no installation is needed.
plotly.express:           A module from plotly containing functions used to create graph plots. To install, run
                          pip install plotly
plotly.graph_objects:     Another module of the plotly library used to create plots.


# User defined inputs:
# area:                   The area of interest, eg. DE, PL etc.
# benchmark_forecast:     'ec00', 'ec12', 'entsoe_da' or 'entsoe_intraday'
# intraday_forecast:      'intraday' or 'intraday_lastec'
# issue_date:             The date where the benchmark-curve (instance curve) was issued.
# time_delta:             Defines how many hours of the intraday curve (absolute curve) that is to be retrieved.
# data_time:              The timestamp of the forecasted value.

"""
from volue_insight_timeseries import Session
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go

# ***********************************
# User defined inputs:
area = "DE"
benchmark_forecast = "ec00"
intraday_forecast = "intraday"
issue_date = "2023-11-26T00:00"
time_delta = 12
data_time = "2023-11-27T10:00"
# ***********************************


def get_input_data(
    benchmark_forecast: str, intraday_forecast: str, area: str
) -> tuple:
    """This function maps the user inputs to available forecasts.

    Args:
        benchmark_forecast: User defined benchmark forecast
        intraday_forecast: User defined intraday forecast
        area: User defined area

    Returns:
        tuple: Two dictionaries containing curve names are returned as a tuple.
    """
    tz = timezone_mapping(area)
    curve_dict = {
        "ec00": {
            "wnd": f"pro {area} wnd ec00 mwh/h {tz} min15 f",
            "spv": f"pro {area} spv ec00 mwh/h {tz} min15 f",
            "con": f"con {area} ec00 mwh/h {tz} min15 f",
            "rdl": f"rdl {area} ec00 mwh/h {tz} min15 f",
        },
        "ec12": {
            "wnd": f"pro {area} wnd ec12 mwh/h {tz} min15 f",
            "spv": f"pro {area} spv ec12 mwh/h {tz} min15 f",
            "con": f"con {area} ec12 mwh/h {tz} min15 f",
            "rdl": f"rdl {area} ec12 mwh/h {tz} min15 f",
        },
        "entsoe_da": {
            "wnd": f"pro {area} wnd da entso-e mwh/h {tz} h f",
            "spv": f"pro {area} spv da entso-e mwh/h {tz} h f",
            "con": f"con {area} da entso-e mwh/h {tz} h f",
            "rdl": f"rdl {area} da entso-e mwh/h {tz} h f",
        },
        "entsoe_intraday": {
            "wnd": f"pro {area} wnd intraday entso-e mwh/h {tz} h f",
            "spv": f"pro {area} spv intraday entso-e mwh/h {tz} h f",
            "con": f"con {area} intraday entso-e mwh/h {tz} h f",
            "rdl": f"rdl {area} intraday entso-e mwh/h {tz} h f",
        },
        "multi-source_forecast": {
            "wnd": f"pro {area} wnd intraday mwh/h {tz} min15 f",
            "spv": f"pro {area} spv intraday mwh/h {tz} min15 f",
            "con": f"con {area} intraday mwh/h {tz} min15 f",
            "rdl": f"rdl {area} intraday mwh/h {tz} min15 f",
        },
        "intraday_lastec": {
            "wnd": f"pro {area} wnd intraday lastec mwh/h {tz} min15 f",
            "spv": f"pro {area} spv intraday lastec mwh/h {tz} min15 f",
            "con": f"con {area} intraday lastec mwh/h {tz} min15 f",
            "rdl": f"rdl {area} intraday mwh/h {tz} min15 f",
        },
    }
    return curve_dict[benchmark_forecast], curve_dict[intraday_forecast]


def getkey() -> Session:
    """This function configures Session from volue_insight_timeseries with local environment variable "WAPI_INI_READ"
    to allow for connection to the Volue Data & Forecasts API.

    Returns:
        session (volue_insight_timeseries.session.Session): A session object that can
        communicate with the Volue Data & Forecasts API.
    """

    config = os.getenv("WAPI_INI_READ")
    session = Session(config_file=config)
    return session


def get_instance_curve(session: Session, curve_name: str, issue_date: str) -> pd.Series:
    """This function retrieves the instance curve released at the determined issue date.
    Args:
    session: Session object to interact with the Volue Data & Forecasts API.
    curve_name: The name of the curve that is to be retrieved as an instance curve.
    issue_date: The user defined date of issue for the instance curve.

    Returns:
        time_series_pandas: Curve data as a pandas time series.
    """
    instance_curve = session.get_curve(name=curve_name)
    time_series = instance_curve.get_instance(issue_date=issue_date)
    time_series_pandas = time_series.to_pandas()
    return time_series_pandas


def get_absolute_curve(
    data_time: pd.Timestamp,
    session: Session,
    curve_name: str,
    delta_hours: pd.Timedelta,
) -> pd.Series:
    """This function retrieves the curve which displays how the forecasted value at timestamp "data_time" develops
    with each release (absolute curve).

    Args:
        data_time: The timestamp of the forecasted value.
        session: Session object to interact with the Volue Data & Forecasts API.
        curve_name: The name of the curve that is to be retrieved as an absolute curve.
        delta_hours: A value that defines how many hours back from the timestamp of data_time to retrieve data.

    Returns:
        time_series_pandas: Absolute curve data as pandas time series.
    """

    date_from = pd.Timestamp(data_time) - pd.Timedelta(hours=delta_hours)
    curve = session.get_curve(name=curve_name)
    time_series = curve.get_absolute(
        issue_date_from=date_from,
        issue_date_to=data_time,
        data_date=data_time,
        issue_frequency="MIN15",
    )
    time_series_pandas = time_series.to_pandas()
    return time_series_pandas


def get_instance_data(
    instance_curves_names: dict, session: Session, issue_date: pd.Timestamp
) -> pd.DataFrame:
    """This function uses the get_instance_curve to retrieve the instance curve data from all benchmark curves,
    then maps it into a dataframe.

    Args:
        instance_curves_names: A dictionary containing all instance curve names (the benchmark curves).
        session: Session object to interact with the Volue Data & Forecasts API.
        issue_date: The user defined date of issue for the instance curve.


    Returns:
        df: A dataframe containing all instance curve data from the benchmark curves.
    """
    df = pd.DataFrame()
    for curve_name in instance_curves_names.values():
        instance_curve = get_instance_curve(
            curve_name=curve_name, session=session, issue_date=issue_date
        )
        instance_curve.name = map_name_to_label(instance_curve.name)
        df = pd.concat([df, instance_curve], axis=1)
    return df


def get_absolute_data(
    absolute_curves_names: str,
    session: Session,
    data_time: pd.Timestamp,
    time_delta: pd.Timedelta,
) -> pd.DataFrame:
    """This function uses the get_absolute_curve to retrieve the absolute curve data from all intraday curves,
    then maps it into a dataframe.

    Args:
        absolute_curves_names: A dictionary containing all absolute curve names (the intraday curves).
        session: Session object to interact with the Volue Data & Forecasts API.
        data_time: The timestamp of the forecasted value.
        time_delta: Defines how many hours of the intraday curve that is to be retrieved.

    Returns:
        df: A dataframe containing all absolute curve data from the intraday curves.
    """

    df = pd.DataFrame()

    for curve_name in absolute_curves_names.values():
        absolute_curve = get_absolute_curve(
            data_time=data_time,
            session=session,
            curve_name=curve_name,
            delta_hours=time_delta,
        )
        absolute_curve.name = map_name_to_label(absolute_curve.name)
        df = pd.concat([df, absolute_curve], axis=1)
    return df


def timezone_mapping(area: str) -> str:
    """This function defines a timezone depending on the area input.

    Args:
        area: User defined area.

    Returns:
        str: The timezone displayed as a string.
    """
    if area.upper() == "TR":
        return "trt"
    elif "IE" in area.upper():
        return "wet"
    else:
        return "cet"


def map_name_to_label(curve_name: str) -> str:
    """This function matches one name from the defined dictionary below with an inputted curve name and returns
    a more readable name.

    Args:
        curve_name: A curve name, for instance: "pro fr wnd ec00 mwh/h cet min15 f 2023-11-26T00:00:00+01:00"

    Returns:
        str: A name from the dictionary generated in this function. Can be used as column names in a df."
    """
    mapping = dict(
        spv="Spv production",
        wnd="Wind production",
        con="Consumption",
        rdl="Residual load",
    )
    return [mapping.get(name, "Undefined") for name in mapping if name in curve_name][0]


def create_dataframe(
    instance_curves_df: dict,
    absolute_curves_df: dict,
    area: str,
    data_time: pd.Timestamp,
) -> pd.DataFrame:
    """This function takes two dataframes as input, instance_curves_df and absolute_curves_df and subtracts each of
    the base forecasts' values at the data time timestamp from each value in the corresponding columns in the
    intraday dataframe.
    Args:
        instance_curves_df: A dataframe containing all retrieved data from all the benchmark curves.
        absolute_curves_df: A dataframe containing all retrieved data from all the intraday curves.
        area: The user defined area.
        data_time: The timestamp of the forecasted value.

    Returns:
        difference_curves: A dataframe containing the difference values between benchmark forecast and intraday
        forecast. Ready to be plotted.
    """
    data_time_timezone = pd.Timestamp(data_time, tz=timezone_mapping(area))
    difference_curves = absolute_curves_df.sub(
        instance_curves_df.loc[data_time_timezone]
    ).dropna()

    # Multiply spv and wind production with -1 to align residual load curve with stacked bar plot
    difference_curves.loc[:, ["Spv production", "Wind production"]] *= -1
    return difference_curves


def plot_difference_curves(
    plot_data: pd.DataFrame,
    benchmark_forecast: str,
    intraday_forecast: str,
    area: str,
):
    """This function plots the data generated in create_dataframe. Production and consumption are plotted as bars,
    but residual load is plotted as a trace/line plot.

    Args:
        plot_data: A pandas dataframe containing the difference between the intraday forecast-values and the
                   benchmark forecast-value.
        benchmark_forecast: The user defined benchmark forecast.
        intraday_forecast: The user defined intraday forecast.
        area: The user defined area.
    """
    color_match = {
        "Spv production": "turquoise",
        "Wind production": "palegreen",
        "Consumption": "green",
    }

    fig = px.bar()

    for i in range(len(plot_data.columns)):
        column_name = plot_data.columns[i]
        column_data = plot_data.iloc[:, i]

        print("plotting:", column_name)

        if column_name == "Residual load":
            fig.add_trace(
                go.Scatter(
                    x=plot_data.index,
                    y=column_data,
                    mode="lines",
                    name=column_name,
                    line=dict(color="red"),
                )
            )
        else:
            fig.add_bar(
                x=plot_data.index,
                y=column_data,
                name=column_name,
                marker_color=color_match[column_name],
            )

    fig.update_layout(
        xaxis=dict(
            rangeslider=dict(visible=True),
        ),
        title=f"Lead time analysis at time {data_time} for area: {area.upper()}. Benchmark forecast: {benchmark_forecast.upper()}. intraday forecast: {intraday_forecast.upper()}",
        yaxis_title="Shift in MW",
        xaxis_title="Time",
    )
    fig.update_layout(title_font=dict(size=25))
    fig.show()
    print("Run successful")


def main():
    """This function runs through the main part of the code."""

    instance_curves_names, absolute_curves_names = get_input_data(
        benchmark_forecast, intraday_forecast, area
    )
    session = getkey()
    instance_curves_df = get_instance_data(
        instance_curves_names=instance_curves_names,
        session=session,
        issue_date=issue_date,
    )
    absolute_curves_df = get_absolute_data(
        absolute_curves_names=absolute_curves_names,
        session=session,
        data_time=data_time,
        time_delta=time_delta,
    )
    plot_data = create_dataframe(
        instance_curves_df, absolute_curves_df, area=area, data_time=data_time
    )
    plot_difference_curves(plot_data, benchmark_forecast, intraday_forecast, area)


if __name__ == "__main__":
    main()
