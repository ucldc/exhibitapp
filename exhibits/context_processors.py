
def settings(request):
    """
    Put selected settings variables into the default template context
    """
    from django.conf import settings
    context = {
        'exhibitBaseTemplate': settings.EXHIBIT_TEMPLATE,
        'thumbnailUrl': settings.THUMBNAIL_URL,
        'calisphere': settings.CALISPHERE,
    }

    return context