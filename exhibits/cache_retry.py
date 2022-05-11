""" logic for cache / retry for solr and JSON from registry
"""

from future import standard_library
standard_library.install_aliases()
from builtins import object
from django.core.cache import cache
from django.conf import settings

from collections import namedtuple
import urllib.request, urllib.error, urllib.parse
from retrying import retry
import requests
import pickle
import hashlib
import json
import itertools

from django.http import JsonResponse

requests.packages.urllib3.disable_warnings()

SOLR_DEFAULTS = {
    'mm': '100%',
    'pf3': 'title',
    'pf': 'text,title',
    'qs': 12,
    'ps': 12,
}

DEFAULT_SOLR_URL = settings.SOLR_URL
SOLR_URL = DEFAULT_SOLR_URL
DEFAULT_SOLR_API_KEY = settings.SOLR_API_KEY
SOLR_API_KEY = settings.SOLR_API_KEY

try:
    for opt in settings.SOLR_OPTS:
        if opt['url'] == DEFAULT_SOLR_URL:
            SOLR_VERSION = opt['version']
except AttributeError:
    SOLR_VERSION = ''

"""
    qf:
        fields and the "boosts" `fieldOne^2.3 fieldTwo fieldThree^0.4`
    mm: (Minimum 'Should' Match)
    qs:
        Query Phrase Slop (in qf fields; affects matching).

    pf: Phrase Fields
	"pf" with the syntax
        field~slop.
        field~slop^boost.
    ps:
	Default amount of slop on phrase queries built with "pf",
	"pf2" and/or "pf3" fields (affects boosting).
    pf2: (Phrase bigram fields)
    ps2: (Phrase bigram slop)
	<!> Solr4.0 As with 'ps' but for 'pf2'. If not specified,
	'ps' will be used.
    pf3 (Phrase trigram fields)
	As with 'pf' but chops the input into tri-grams, e.g. "the
	brown fox jumped" is queried as "the brown fox" "brown fox
	jumped"
    ps3 (Phrase trigram slop)
    tie (Tie breaker)
	Float value to use as tiebreaker in DisjunctionMaxQueries
	(should be something much less than 1)
        Typically a low value (ie: 0.1) is useful.

"""

def switch_solr(request):
    solr_switcher(request.GET.get('v', 'default'))
    return JsonResponse(
        {'current_solr': SOLR_VERSION})

def solr_switcher(version):
    if not settings.CALISPHERE:
        switch = [opt for opt in settings.SOLR_OPTS if opt['version'] == version][0]
        if switch:
            global SOLR_URL, SOLR_API_KEY, SOLR_VERSION
            SOLR_URL = switch['url']
            SOLR_API_KEY = switch['api_key']
            SOLR_VERSION = switch['version']


SolrResults = namedtuple(
    'SolrResults', 'results header numFound facet_counts nextCursorMark')

SolrDocs = namedtuple(
    'SolrDocs', 'results header numFound')

def SOLR(**params):
    # replacement for edsu's solrpy based stuff
    solr_url = '{}/query/'.format(SOLR_URL)
    solr_auth = {'X-Authentication-Token': SOLR_API_KEY}
    # Clean up optional parameters to match SOLR spec
    query = {}
    for key, value in list(params.items()):
        key = key.replace('_', '.')
        query.update({key: value})
    res = requests.post(solr_url, headers=solr_auth, data=query, verify=False)
    res.raise_for_status()
    results = json.loads(res.content.decode('utf-8'))
    facet_counts = results.get('facet_counts', {})
    for key, value in list(facet_counts.get('facet_fields', {}).items()):
        # Make facet fields match edsu with grouper recipe
        facet_counts['facet_fields'][key] = dict(
            itertools.zip_longest(*[iter(value)] * 2, fillvalue=""))

    return SolrResults(
        results['response']['docs'],
        results['responseHeader'],
        results['response']['numFound'],
        facet_counts,
        results.get('nextCursorMark'),
    )


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


# dummy class for holding cached data
class SolrCache(object):
    pass


def SOLR_get(ids):
    solr_url = '{}/get'.format(SOLR_URL)
    solr_auth = {'X-Authentication-Token': SOLR_API_KEY}
    query = {'ids': ','.join(ids)}
    resp = requests.get(solr_url, headers=solr_auth, data=query, verify=False)
    results = json.loads(resp.content.decode('utf-8'))
    return SolrDocs(
        results['response']['docs'],
        resp.status_code,
        results['response']['numFound'],
    )

# wrapper function for solr queries
@retry(stop_max_delay=3000)  # milliseconds
def SOLR_select(**kwargs):
    kwargs.update(SOLR_DEFAULTS)
    # look in the cache
    key = 'SOLR_select_{1}_{0}'.format(kwargs_md5(**kwargs), SOLR_VERSION)
    sc = cache.get(key)
    if not sc:
        # do the solr look up
        sr = SOLR(**kwargs)
        # copy attributes that can be pickled to new object
        sc = SolrCache()
        sc.results = sr.results
        sc.header = sr.header
        sc.facet_counts = getattr(sr, 'facet_counts', None)
        sc.numFound = sr.numFound
        cache.set(key, sc, settings.DJANGO_CACHE_TIMEOUT)  # seconds
    return sc


@retry(stop_max_delay=3000)
def SOLR_raw(**kwargs):
    kwargs.update(SOLR_DEFAULTS)
    # look in the cache
    key = 'SOLR_raw_{0}'.format(kwargs_md5(**kwargs))
    sr = cache.get(key)
    if not sr:
        # do the solr look up
        solr_url = '{}/query/'.format(settings.SOLR_URL)
        solr_auth = {'X-Authentication-Token': settings.SOLR_API_KEY}
        # Clean up optional parameters to match SOLR spec
        query = {}
        for key, value in list(kwargs.items()):
            key = key.replace('_', '.')
            query.update({key: value})
        res = requests.get(
            solr_url, headers=solr_auth, params=query, verify=False)
        res.raise_for_status()
        sr = res.content
        cache.set(key, sr, settings.DJANGO_CACHE_TIMEOUT)  # seconds
    return sr


@retry(stop_max_delay=3000)
def SOLR_select_nocache(**kwargs):
    kwargs.update(SOLR_DEFAULTS)
    sr = SOLR(**kwargs)
    return sr
