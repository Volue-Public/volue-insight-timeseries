"""
This simple example reads paired data from a PairedList curve
PairedList curves contain paired values like price-volume pairs.
"""

import volue_insight_timeseries as vit
import matplotlib.pyplot as plt

############################################
# Insert the path to your config file here!
my_config_file = 'path/to/your/config.ini'
############################################


# Create a session to connect to Volue Insight API
session = vit.Session(config_file=my_config_file)


# Define curve name to read
curve_name = "YOUR_PAIRED_LIST_CURVE_NAME"
# Get the curve
curve = session.get_curve(name=curve_name)

# Get the available tags for this curve
tags = curve.get_tags()
print('Available tags:', tags)

# Read paired data for a specific date range
paired_data = curve.get_data(
    data_from='2025-12-18',
    data_to='2025-12-19',
    with_data=True
)

# Get the first instance and convert to pandas DataFrame
first_instance = paired_data[0]
df = first_instance.to_pandas()

print(df.head())

# Plot the paired data
plt.scatter(df['price'], df['volume'])
plt.show()