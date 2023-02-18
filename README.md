# Django Requests Tracker

<img src="https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/bensi94/0fbe0bd93d1307b7bb1096206b7817fa/raw/covbadge.json" alt="Test">

A convenient Django development tool based on the great [`Django Debug Toolbar`](https://github.com/jazzband/django-debug-toolbar) but aimed towards rest API development. It collects and displays information on requests, responses, SQL queries, headers, Django settings and more.

## Table of contents
1. [Features](#features)
    1. [Requests list](#requests-list)
    2. [Request details](#request-details)
2. [The example Project](#the-example-project)
3. [Installation](#installation)
    1. [Install the package](#install-the-package)
    2. [Configure project settings](#configure-project-settings)
    3. [Configure URLs](#configure-urls)
    4. [Optional: Configure static content for WSGI and ASGI servers, e.g. Uvicorn for async Django](#configure-static-content)
4. [Configuration](#configuration)
   1. [IGNORE_SQL_PATTERNS](#ignore_sql_patterns)
   2. [IGNORE_PATHS_PATTERNS](#ignore_paths_patterns)
   3. [ENABLE_STACKTRACES](#enable_stacktraces)
   4. [HIDE_IN_STACKTRACES](#hide_in_stacktraces)
   5. [SQL_WARNING_THRESHOLD](#sql_warning_threshold)
   6. [TRACK_SQL](#track_sql)

## Features

### Requests list

Django Requests Tracker registers every request sent to your Django application and displays them in a tidy list. Each element in the list contains information about the request's HTTP method, path, Django view, status code, database information and query count and execution time and duration.

The requests list can be:
* Searched by *path*, *Django view*, *sql* and *headers*. The search is quite simple and a request is only filtered from the list if the search term does not exist in any of theses elements.
* Ordered in ascending and descending order by *time*, *duration*, *Django view*, *query count*, *similar query count* and *duplicate query count*.
* Auto-refreshed so that new requests will automatically show up in the list.
* Manually refreshed.
* Cleared.

#### The requests list in action 🎥

![requests-list](https://user-images.githubusercontent.com/20007971/215617783-5511c6cd-0e99-4d0d-8260-e269b7977c87.gif)

### Request details

Each list element can be clicked where further information collected about the request such as SQL queries and headers can be found.

#### SQL queries

In request details, every SQL query executed in the context of the Django request should be shown, along with the execution time and a timeline bar that shows how big a chunk of the total time belongs to the given query. A stacktrace is shown for each query that helps with finding the origin of it.

Some queries are labelled with a tag `X similar queries` or `X duplicate queries` this can often indicate a problem and can be very handy when debugging or in development.

* `Similar Queries` means that the same query is executed more than once but with different parameters. This can for example happen when iterating over a list of IDs and fetching one item by ID at a time.
* `Duplicate Queries` means that the exact same query with the same parameters is executed more than once. This can for example happen when iterating over a list child items and fetching same parent multiple times. Also known as an N-plus-1 query which is quite common problem with ORMs.

#### The request details view in action 🎥
![request-details](https://user-images.githubusercontent.com/20007971/215625549-50a0e1e1-f5f2-47c1-a36e-bb5a7cb9fd75.gif)


### Django Settings

Django settings very often contain some logic, and usage of environment variables and can even be spread out over multiple files. So it can be very beneficial to be able to see the current computed settings being used in the running process. Django Requests Tracker offers a simple way to view this. The view can be accessed by clicking on `Django settings` in the right corner of the requests tracker view.

All information determined to be sensitive, such as keys and passwords, are masked in the displayed settings.

<img width="1470" alt="Screenshot 2023-01-31 at 00 24 32" src="https://user-images.githubusercontent.com/20007971/215627287-4d62cc7d-1679-4fee-ad20-c52b59dccf34.png">

## The Example Project

This repository includes an [example project](example_project) to try out the package and see how it works. It can also be a great reference when adding the package to your project. To try it out, clone this project and follow the instructions on the [example project README](example_project/README.md)

## Installation

If any of the following steps are unclear, check out the [Example Project](example_project) for reference.

### Install the package

```bash
pip install requests-tracker
```

or install with you're chosen package tool, e.g.
[poetry](https://python-poetry.org/),
[pipenv](https://pipenv.pypa.io/en/latest/), etc.

### Configure project settings

#### Settings prerequisites

First, ensure that `django.contrib.staticfiles` is in your `INSTALLED_APPS` setting and configured properly:
```python
INSTALLED_APPS = [
    # ...
    "django.contrib.staticfiles",
    # ...
]

STATIC_URL = "static/"
```

Second, ensure that your `TEMPLATES` setting contains a `DjangoTemplates` backend whose `APP_DIRS` options is set to True:
```python
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        # ...
    }
]
```

#### Install the app, add middleware and configure internal ips

* Add `requests_tracker` to your `INSTALLED_APPS` setting.
* Add `requests_tracker.middleware.requests_tracker_middleware` to your `MIDDLEWARE` setting.
* Add your internal IP addresses to `INTERNAL_IPS` setting.
```python
if DEBUG:
    INSTALLED_APPS += ["requests_tracker"]
    MIDDLEWARE += ["requests_tracker.middleware.requests_tracker_middleware"]
    INTERNAL_IPS = ["127.0.0.1"]
```

🚨 ️&nbsp; It's recommended to only configure these settings in DEBUG mode.
Even though Django Requests Tracker will only track requests in DEBUG mode
it's still a good practice to only have it installed in DEBUG mode.

### Configure URLs

Add Django Requests Tracker URLs to your project's URLconf:
```python
if settings.DEBUG:
    urlpatterns += [path("__requests_tracker__/", include("requests_tracker.urls"))]
```

🚨️&nbsp; Again it's recommended to only add the URLs in DEBUG mode.


### Optional: Configure static content for WSGI and ASGI servers, e.g. Uvicorn for async Django <a name="configure-static-content"></a>

#### Add static root to settings
```python
# 🚨 Your project might not include BASE_DIR setting but likely some variation of it 🚨
BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_ROOT = os.path.join(BASE_DIR, "static")
```

#### Add static root URLs to your project's URLconf:
```python
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
```

#### Collect static files
```console
python manage.py collectstatic
```

## Configuration

Django Requests Tracker provides a few very simple settings. The settings are applied by setting `REQUESTS_TRACKER_CONFIG` setting in your `settings.py` file. `REQUESTS_TRACKER_CONFIG` takes a dictonary. Example:

```python
# settings.py

REQUESTS_TRACKER_CONFIG = {
    "IGNORE_PATHS_PATTERNS": (".*/api/keep-alive.*",),
    "ENABLE_STACKTRACES": False",
}
```

### `IGNORE_SQL_PATTERNS`

Takes a tuple of strings. Each string is a regular expression pattern.
If a SQL query matches any of the patterns it will be ignored and not
shown in the requests list or request details.

Default: `()`

Example:
```python
REQUESTS_TRACKER_CONFIG = {
    "IGNORE_SQL_PATTERNS": (
        r"^SELECT .* FROM django_migrations WHERE app = 'requests_tracker'",
        r"^SELECT .* FROM django_migrations WHERE app = 'auth'",
    ),
}
```

### `IGNORE_PATHS_PATTERNS`

Takes a tuple of strings. Each string is a regular expression pattern.
If a request path matches any of the patterns it will be ignored and not tracked.

Default: `()`

Example:
```python
REQUESTS_TRACKER_CONFIG = {
    "IGNORE_PATHS_PATTERNS": (
        r".*/api/keep-alive.*",
    ),
}
```

### `SQL_WARNING_THRESHOLD`

Represents the threshold in milliseconds after which a SQL query is considered slow and
will be marked with a warning label in the SQL list.

Default: `500` (500 milliseconds)

Example:
```python
REQUESTS_TRACKER_CONFIG = {
    "SQL_WARNING_THRESHOLD": 50,
}
```

### `ENABLE_STACKTRACES`

If set to `False` stacktraces will not be shown in the request details view.

Default: `True`

### `HIDE_IN_STACKTRACES`

Takes a tuple of strings. Each string represents a module name. If a module name is found
in a stacktrace that part of the stacktrace will be hidden.

Default:
```python
(
     "socketserver",
     "threading",
     "wsgiref",
     "requests_tracker",
     "django.db",
     "django.core.handlers",
     "django.core.servers",
     "django.utils.decorators",
     "django.utils.deprecation",
     "django.utils.functional",
)
```

### `TRACK_SQL`

If set to `False` SQL queries will not be tracked.

Default: `True`
