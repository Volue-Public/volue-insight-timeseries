# volue-insight-timeseries
Volue Insight API python library for working with timeseries.

This library is meant as a simple toolkit for working with data from
https://api.volueinsight.com/ (or equivalent services). Note that access
is based on having a valid Volue Insight account. Please contact
sales.insight@volue.com in order to get a trial account.

The library is tested against Python 3.9, 3.10, 3.11 and 3.12 - we recommend using 
the latest Python version.


## Documentation

The 
[documentation](https://wattsight-volue-insight-timeseries.readthedocs-hosted.com/en/master/) 
with various 
[examples](https://wattsight-volue-insight-timeseries.readthedocs-hosted.com/en/master/examples.html)
is hosted on Read the Docs.

## Installation

You can simply install/update the latest version of Volue Insight API python
library with pip.
Start a terminal (a shell) and use the following command

```bash
pip install -U volue-insight-timeseries
```

### Pin this package
We strongly recommend to pin your dependency on our package, since we will do
changes to the package as we introduce new features, fix issues etc. See example
below. At least make sure you lock down the major version in your
requirements.txt file in order to prevent your code to break when we do
breaking changes.

```bash
# your requirements.txt

volue-insight-timeseries==1.0.0 # Good
volue-insight-timeseries # Bad
```

We follow [Semantic Versioning](https://semver.org/spec/v2.0.0-rc.2.html)
principles to communicate the type of change from one version to the next,
together with [release notes](https://github.com/volueinsight/volue-insight-timeseries/releases).

## Migrating from wapi-python
If you previously have used wapi-python, you should switch to use this package
going forward. We will not add any new features to wapi-python, it is only in 
the event of a severe bug that we will do any changes to it.

These are the steps you will have to do in order to successfully
make the switch. 

* Use Python 3.9, 3.10, 3.11 or 3.12
* Use Pandas 1.5.0 or newer
* Use [zoneinfo](https://docs.python.org/3/library/zoneinfo.html), not pytz for handling time zone information

### Example of migrating an existing script
Assume you want to migrate the script below. It is a very simple script to
highlight things that are changing, not a recommended way to write production
code.

```python
# python 3.9.8
# pip install wapi-python==0.7.15
# pip install python-dotenv==1.0.1
#
# ---
# .env file contents
# CLIENT_ID=your-client-id
# CLIENT_SECRET=your-client-secret

import os
import wapi
from wapi.util import TS
from wapi.curves import InstanceCurve
from dotenv import load_dotenv

load_dotenv()
session = wapi.Session(client_id=(os.environ['CLIENT_ID']),
                       client_secret=(os.environ['CLIENT_SECRET']))

results = session.search(name="tt no2 con ec00 °c cet min15 f")
if results:
    instance_curve: InstanceCurve = results[0]
    data: TS = instance_curve.get_latest(data_to="2030-04-01T04:00Z")
    print(f"Curve type: {data.curve_type}")
    print(f"Time zone class of curve data: {type(data.tz)}")

# Output
# Curve type: INSTANCES
# Time zone class of curve data: <class 'pytz.tzfile.CET'>
```

The migrated script is below

```python
# python 3.9.8
# pip install volue-insight-timeseries==1.2.0
# pip install python-dotenv==1.0.1
#
# ---
# .env file contents
# CLIENT_ID=your-client-id
# CLIENT_SECRET=your-client-secret

import os
import volue_insight_timeseries as vit
from volue_insight_timeseries.util import TS
from volue_insight_timeseries.curves import InstanceCurve
from dotenv import load_dotenv

load_dotenv()
session = vit.Session(client_id=(os.environ['CLIENT_ID']),
                      client_secret=(os.environ['CLIENT_SECRET']))

results = session.search(name="tt no2 con ec00 °c cet min15 f")
if results:
    instance_curve: InstanceCurve = results[0]
    data: TS = instance_curve.get_latest(data_to="2030-04-01T04:00Z")
    print(f"Curve type: {data.curve_type}")
    print(f"Time zone class of curve data: {type(data.tz)}")

# Output
# Curve type: INSTANCES
# Time zone class of curve data: <class 'zoneinfo.ZoneInfo'>
```

## Copyright (MIT License)

Copyright (c) 2018-2024 Volue Insight AS

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
