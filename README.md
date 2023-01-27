# Django Requests Tracker

<img src="https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/bensi94/0fbe0bd93d1307b7bb1096206b7817fa/raw/covbadge.json" alt="Test">

A convenient Django development tool based on the great [`Django Debug Toolbar`](https://github.com/jazzband/django-debug-toolbar) but aimed towards rest API development. It collects and displays information on requests, responses, SQL queries, headers, Django settings and more.


## Installation

If any of the following steps are unclear, check out the [Example Project](example_project) for reference.

### Install the package

```bash
pip install django-requests-tracker
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


### Optional: Configure static content for WSGI and ASGI servers, e.g. Uvicorn for async Django

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
