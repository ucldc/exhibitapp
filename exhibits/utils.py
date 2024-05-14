import pickle
import hashlib
import json
import urllib.request
import urllib.error
import urllib.parse

from retrying import retry
from django.core.cache import cache
from django.conf import settings
from functools import wraps
from django.views.decorators.cache import cache_page


# create a hash for a cache key
def kwargs_md5(**kwargs):
    m = hashlib.md5()
    m.update(pickle.dumps(kwargs))
    return m.hexdigest()


# wrapper function for json.loads(urllib2.urlopen)
@retry(wait_exponential_multiplier=2, stop_max_delay=10000)  # milliseconds
def json_loads_url(url_or_req):
    key = kwargs_md5(key='json_loads_url', url=url_or_req)
    data = cache.get(key)
    if not data:
        try:
            data = json.loads(
                urllib.request.urlopen(url_or_req).read().decode('utf-8'))
        except urllib.error.HTTPError:
            data = {}
    return data


# https://stackoverflow.com/questions/27347921/in-django-can-per-view-cache-decorator-be-session-dependent-for-a-b-testings
def cache_by_session_state(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        index = request.session.get('index')

        if (
            not index or
            (index == 'solr' and not settings.SOLR_URL) or
            (index == 'es' and not settings.ES_HOST)
        ):
            # no index happens when we have a first-time visitor;
            # index variables without corresponding settings variables
            # can happen in development when there's a persistent
            # browser session across a change in settings configuration
            index = settings.DEFAULT_INDEX
            request.session['index'] = index

        cached = cache_page(60 * 1, key_prefix=index)(func)
        return cached(request, *args, **kwargs)
    return wrapper
