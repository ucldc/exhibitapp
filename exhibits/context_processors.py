from exhibits import cache_retry

def settings(request):
    """
    Put selected settings variables into the default template context
    """
    from django.conf import settings
    context = {
        'exhibitBaseTemplate': settings.EXHIBIT_TEMPLATE,
        'thumbnailUrl': settings.THUMBNAIL_URL,
        'calisphere': settings.CALISPHERE,
        'solr_opts': None,
        'solr_version': None
    }

    try:
        version_names = [{
            'version': opt['version'],
            'display_name': opt['display_name']
        } for opt in settings.SOLR_OPTS]
        context['solr_opts'] = version_names
        context['solr_version'] = cache_retry.SOLR_VERSION
    except AttributeError:
        pass

    return context