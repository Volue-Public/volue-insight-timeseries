# volue-insight-timeseries
Volue Data & Forecasts API python library for working with timeseries.

This library is meant as a simple toolkit for working with data from
https://data-forecasts.volue.com/ (or equivalent services). Note that access
is based on having a valid Volue Data & Forecasts account. To get a trial account,
use the "Get in touch" form at https://www.volue.com/data-and-forecasts.

The library is tested against Python 3.11, 3.12, 3.13 and 3.14. Please only use either of these python versions.


## Documentation

The 
[documentation](https://docs.volue.com/data-and-forecasts/volue-insight-timeseries/) 
with various 
[examples](https://docs.volue.com/data-and-forecasts/volue-insight-timeseries/guides/examples)

### How to edit documentation

Documentation source can be updated in the internal repo: 
https://github.com/Volue/sirius-core-py-docs

## Installation

You can simply install/update the latest version of Volue Data & Forecasts API python
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

volue-insight-timeseries==X.Y.Z # Good - Pin to specific version
volue-insight-timeseries # Bad - Unpinned, may break on updates
```

We follow [Semantic Versioning](https://semver.org/spec/v2.0.0-rc.2.html)
principles to communicate the type of change from one version to the next,
together with [release notes](https://github.com/Volue-Public/volue-insight-timeseries/releases).

## Connection settings

### Your own requests session
Pass your own `requests.Session` when you need a proxy, a CA bundle, a client
certificate or a larger connection pool, and cannot set them through
environment variables such as `HTTPS_PROXY` or `REQUESTS_CA_BUNDLE`. All
requests, authentication included, are sent through it.

```python
import requests
import volue_insight_timeseries as vit

http_session = requests.Session()
http_session.proxies = {'https': 'http://proxy.example.com:8080'}
http_session.verify = '/path/to/ca-bundle.pem'

session = vit.Session(config_file='config.ini', requests_session=http_session)
```

### Retries
By default, a request that times out, fails to connect or gets a 408 or 5xx
response is retried 4 times, with 0.5 seconds between attempts. Change the
number with `retries`, or pass a urllib3 `Retry` for other rules, such as
backoff:

```python
from urllib3.util import Retry

session = vit.Session(config_file='config.ini', retries=2)
session = vit.Session(config_file='config.ini',
                      retries=Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504],
                                    allowed_methods=None, raise_on_status=False))
```

`retries=0` turns retries off. Use it when your `requests_session` already
retries through a urllib3 `Retry` on its adapters, or requests are retried at
both levels.

## Migrating from wapi-python
If you previously have used wapi-python, you should switch to use this package
going forward. We will not add any new features to wapi-python, it is only in 
the event of a severe bug that we will do any changes to it.

These are the steps you will have to do in order to successfully
make the switch. 

* Use Python 3.11, 3.12, 3.13 or 3.14
* Use Pandas 1.5.0 or newer for python 3.11. Use Pandas 2.1.1 or newer for python 3.12. Use Pandas 2.2.3 or newer for python 3.13. Use Pandas 2.3.3 or newer for python 3.14
* Use [zoneinfo](https://docs.python.org/3/library/zoneinfo.html), not pytz for handling time zone information

### Example of migrating an existing script
Assume you want to migrate the script below. It is a very simple script to
highlight things that are changing, not a recommended way to write production
code.

```python
# python 3.11.17
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
# python 3.11.17
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
