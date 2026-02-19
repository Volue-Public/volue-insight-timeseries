"""
Fetching multiple instances with custom filters in a batch request.

If you cannot use the predefined issue date filters, you can also search for
all instances and filter them yourself with an ad-hoc function, in order
fetch instances in batches.

Beware that batch fetching may lead to fetching more datapoints than the API
allows in one request or putting unreasonable load on the api.
Read our docs on best practice to make sure you follow our guidelines.
"""

from datetime import datetime

from volue_insight_timeseries import Session
from volue_insight_timeseries.util import TS
from volue_insight_timeseries.curves import InstanceCurve

## INPUTS
################################################
# Insert the path to your config file here!
my_config_file = 'path/to/your/config.ini'

# Create a session to Connect to Volue Insight API
session = Session(config_file=my_config_file)


def filter_instances(instances: list[TS]):
    # filter instances however you like, example below which only keeps
    # instances with issue date from hours 10, 11 and 12
    filtered_instances = []
    for instance in instances:
        issue_date_dt: datetime = datetime.fromisoformat(instance.issue_date)
        if issue_date_dt.hour in range(10, 12):
            filtered_instances.append(instance.issue_date)

    return filtered_instances


curve_name = "cap fr nuc outage umm mw cet min15 f"
curve: InstanceCurve = session.get_curve(name=curve_name)

# Note: you do should not fetch the data at this stage
instances_without_data = curve.search_instances(issue_date_from="2026-02-14",
                                                issue_date_to="2026-02-16",
                                                with_data=False)

print(f"Total instances count: {len(instances_without_data)}")
filtered_instances = filter_instances(instances_without_data)
print(f"Filtered instances count: {len(filtered_instances)}")

# fetch the data for the filtered instances. Use data_from and data_to if you
# want to further limit the time range of the data you fetch
instances_with_data = curve.search_instances(issue_dates=filtered_instances,
                                             with_data=True)
