from django import template

register = template.Library()

@register.simple_tag
# Exhibit
def exhibit_lockup(exhibit, *args):
    return exhibit.exhibit_lockup(*args)

@register.simple_tag
# Exhibit; unused
def exhibit_lockup_sm(exhibit, *args):
    return exhibit.exhibit_lockup_sm(*args)

@register.simple_tag
# Exhibit, HistoricalEssay, LessonPlan, Theme
def social_media_card(obj, *args):
    return obj.social_media_card(*args)

@register.simple_tag
# HistoricalEssay, LessonPlan
def lockup_image(obj, *args):
    return obj.lockup(*args)

@register.simple_tag
def theme_lockup(theme, *args):
    return theme.theme_lockup(*args)

@register.simple_tag
def indexed_data(exhibit_item, *args):
    return exhibit_item.indexedData(*args)

# TODO: ALSO NEED TO IMPORT CUSTOM TEMPLATE TAGS EVERYWHERE THEY ARE USED
