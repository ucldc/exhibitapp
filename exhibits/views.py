

from builtins import range
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from exhibits.models import *
from itertools import chain
from django.conf import settings
from exhibits.cache_retry import SOLR_get_list
import random
import json
from exhibits.utils import cache_by_session_state

@cache_by_session_state
def calCultures(request):
    california_cultures = Theme.objects.filter(title__icontains='California Cultures').order_by('title')

    unique_historical_essays = HistoricalEssay.objects.filter(historicalessaytheme__theme__in=california_cultures).values_list('title', 'id').distinct()
    historical_essays = []
    for (title, key) in unique_historical_essays:
        historical_essays.append(HistoricalEssay.objects.get(pk=key))

    unique_lesson_plans = LessonPlan.objects.filter(lessonplantheme__theme__in=california_cultures).values_list('title', 'id').distinct()
    lesson_plans = []
    for (title, key) in unique_lesson_plans:
        lesson_plans.append(LessonPlan.objects.get(pk=key))

    return render(request, 'exhibits/calCultures.html', {
        'california_cultures': california_cultures, 
        'historical_essays': historical_essays,
        'lesson_plans': lesson_plans
    })

@cache_by_session_state
def exhibitRandom(request):
    exhibits = Exhibit.objects.all()
    themes = Theme.objects.all()
    exhibit_theme_list = list(chain(exhibits, themes))
    random.shuffle(exhibit_theme_list)

    exhibit_theme_list_by_fives = []
    sublist = []
    count = 0

    for index, item in enumerate(exhibit_theme_list):
        if isinstance(item, Exhibit):
            if count < 5:
                sublist.append(('exhibit', item))
                count += 1
            else:
                exhibit_theme_list_by_fives.append(sublist)
                sublist = [('exhibit', item)]
                count = 1
        elif isinstance(item, Theme):
            if count < 4:
                sublist.append(('theme', item))
                count +=2
            elif count < 5:
                # find next instance of exhibit and swap this theme for that exhibit
                for swap in range(index+1, len(exhibit_theme_list)):
                    if isinstance(exhibit_theme_list[swap], Exhibit):
                        tmp = exhibit_theme_list[swap]
                        exhibit_theme_list[swap] = exhibit_theme_list[index]
                        exhibit_theme_list[index] = tmp
                        break

                if isinstance(exhibit_theme_list[index], Exhibit):
                    sublist.append(('exhibit', exhibit_theme_list[index]))
                    count += 1
                else:
                    # haven't found anything to swap with, so this will be a short row
                    exhibit_theme_list_by_fives.append(sublist)
                    sublist = [('theme', item)]
                    count = 2
            else:
                exhibit_theme_list_by_fives.append(sublist)
                sublist = [('theme', item)]
                count = 2

    exhibit_theme_list_by_fives.append(sublist)

    return render(request, 'exhibits/exhibitRandomExplore.html', {'sets': exhibit_theme_list_by_fives, 'sets_standard': exhibit_theme_list})

@cache_by_session_state
def exhibitSearch(request):
    if request.method == 'GET' and len(request.GET.getlist('title')) > 0:
        exhibits = Exhibit.objects.filter(title__icontains=request.GET['title']).order_by('title')
        return render(request, 'exhibits/exhibitSearch.html', {'searchTerm': request.GET['title'], 'exhibits': exhibits})
    else: 
        exhibits = Exhibit.objects.all().order_by('title')
        return render(request, 'exhibits/exhibitSearch.html', {'searchTerm': '', 'exhibits': exhibits})

@cache_by_session_state
def exhibitDirectory(request, category='search'):
    if category in list(category for (category, display) in Theme.CATEGORY_CHOICES):
        themes = Theme.objects.filter(category=category).order_by('sort_title')
        collated = []
        for theme in themes:
            exhibits = Exhibit.objects.filter(exhibittheme__theme=theme)
            collated.append((theme, exhibits))
        return render(request, 'exhibits/exhibitDirectory.html', {'themes': collated, 'categories': Theme.CATEGORY_CHOICES, 'selected': category})
        
    if category == 'all': 
        exhibits = Exhibit.objects.all().order_by('title')
    if category == 'uncategorized':

        # if previewing exhibits, only show in uncategorized those exhibits which are not hooked up to a theme
        if settings.EXHIBIT_PREVIEW:
            exhibits = Exhibit.objects.filter(exhibittheme__isnull=True)
        # if showing exhibits on production, show both exhibits which are not hooked up to a theme
        # AND exhibits which are hooked up to a theme, but the theme is unpublished.
        else:
            exhibitsWithNoTheme = Exhibit.objects.filter(exhibittheme__isnull=True)
            exhibitsWithUnpublishedTheme = Exhibit.objects.filter(exhibittheme__theme__publish=False)
            exhibits = exhibitsWithNoTheme | exhibitsWithUnpublishedTheme

    return render(request, 'exhibits/exhibitDirectory.html', {'themes': [{'', exhibits}], 'categories': Theme.CATEGORY_CHOICES, 'selected': category})

@cache_by_session_state
def themeDirectory(request):
    jarda = Theme.objects.get(slug='jarda')
    california_cultures = Theme.objects.filter(title__icontains='California Cultures').order_by('title')
    california_history = Theme.objects.exclude(title__icontains='California Cultures').exclude(slug='jarda')
    return render(request, 'exhibits/themeDirectory.html', {'jarda': jarda, 'california_cultures': california_cultures, 'california_history': california_history})

@cache_by_session_state
def lessonPlanDirectory(request):
    lessonPlans = LessonPlan.objects.all()
    historicalEssays = HistoricalEssay.objects.all()
    return render(request, 'exhibits/for-teachers.html', {'lessonPlans': lessonPlans, 'historicalEssays': historicalEssays})

@cache_by_session_state
def itemView(request, exhibit_id, item_id):
    fromExhibitPage = request.META.get("HTTP_X_EXHIBIT_ITEM")
    exhibitItem = get_object_or_404(ExhibitItem, item_id=item_id, exhibit=exhibit_id)
    try:
        nextItem = ExhibitItem.objects.get(exhibit=exhibit_id, order=exhibitItem.order+1)
    except ObjectDoesNotExist:
        nextItem = None
    try:
        prevItem = ExhibitItem.objects.get(exhibit=exhibit_id, order=exhibitItem.order-1)
    except ObjectDoesNotExist:
        prevItem = None

    if fromExhibitPage and settings.CALISPHERE:
        return render(request, 'exhibits/itemView.html', {'exhibitItem': exhibitItem, 'nextItem': nextItem, 'prevItem': prevItem})
    else:
        exhibit = get_object_or_404(Exhibit, pk=exhibit_id)
        exhibitItems = exhibit.exhibititem_set.all().order_by('order')
        exhibitListing = []
        for theme in exhibit.published_themes().all():
            exhibits = theme.theme.published_exhibits().exclude(exhibit=exhibit).order_by('order')
            if exhibits.count() > 0:
                exhibitListing.append((theme.theme, exhibits))
        return render(request, 'exhibits/itemView.html',
        {'exhibit': exhibit, 'q': '', 'exhibitItems': exhibitItems, 'relatedExhibitsByTheme': exhibitListing, 'exhibitItem': exhibitItem, 'nextItem': nextItem, 'prevItem': prevItem})

@cache_by_session_state
def lessonPlanItemView(request, lesson_id, item_id):
    fromLessonPage = request.META.get("HTTP_X_EXHIBIT_ITEM")
    exhibitItem = get_object_or_404(ExhibitItem, item_id=item_id, lesson_plan=lesson_id)
    try:
        nextItem = ExhibitItem.objects.get(lesson_plan=lesson_id, lesson_plan_order=exhibitItem.lesson_plan_order+1)
    except ObjectDoesNotExist:
        nextItem = None
    try:
        prevItem = ExhibitItem.objects.get(lesson_plan=lesson_id, lesson_plan_order=exhibitItem.lesson_plan_order-1)
    except ObjectDoesNotExist:
        prevItem = None

    if fromLessonPage:
        return render(request, 'exhibits/lessonItemView.html', {'exhibitItem': exhibitItem, 'nextItem': nextItem, 'prevItem': prevItem})
    else:
        lesson = get_object_or_404(LessonPlan, pk=lesson_id)
        exhibitItems = lesson.exhibititem_set.all().order_by('lesson_plan_order')
        return render(request, 'exhibits/lessonItemView.html',
        {'lessonPlan': lesson, 'q': '', 'exhibitItems': exhibitItems, 'exhibitItem': exhibitItem, 'nextItem': nextItem, 'prevItem': prevItem})

@cache_by_session_state
def exhibitView(request, exhibit_id, exhibit_slug):
    fromExhibitPage = request.META.get("HTTP_X_EXHIBIT_ITEM")
    if fromExhibitPage and settings.CALISPHERE:
        return render(request, 'exhibits/pjaxTemplates/pjax-exhibit-item.html')

    exhibit = get_object_or_404(Exhibit, pk=exhibit_id)
    if exhibit_slug != exhibit.slug:
        return redirect(exhibit)

    exhibitItems = exhibit.exhibititem_set.all().order_by('order')
    exhibitListing = []
    for theme in exhibit.published_themes().all():
        exhibits = theme.theme.published_exhibits().exclude(exhibit=exhibit).order_by('order')
        if exhibits.count() > 0:
            exhibitListing.append((theme.theme, exhibits))

    return render(request, 'exhibits/exhibitView.html',
    {'exhibit': exhibit, 'q': '', 'exhibitItems': exhibitItems, 'relatedExhibitsByTheme': exhibitListing})

@cache_by_session_state
def essayView(request, essay_id, essay_slug):
    essay = get_object_or_404(HistoricalEssay, pk=essay_id)
    if essay_slug != essay.slug:
        return redirect(essay)

    return render(request, 'exhibits/essayView.html', {'essay': essay, 'q': ''})

@cache_by_session_state
def themeView(request, theme_id, theme_slug):
    theme = get_object_or_404(Theme, pk=theme_id)
    if theme_slug != theme.slug:
        return redirect(theme)

    exhibitListing = theme.published_exhibits().all().order_by('order')
    return render(request, 'exhibits/themeView.html', {'theme': theme, 'relatedExhibits': exhibitListing})

@cache_by_session_state
def lessonPlanView(request, lesson_id, lesson_slug):
    fromLessonPage = request.META.get("HTTP_X_EXHIBIT_ITEM")
    if fromLessonPage and settings.CALISPHERE:
        return render(request, 'exhibits/pjaxTemplates/pjax-exhibit-item.html')

    lesson = get_object_or_404(LessonPlan, pk=lesson_id)
    if lesson_slug != lesson.slug:
        return redirect(lesson)

    exhibitItems = lesson.exhibititem_set.all().order_by('lesson_plan_order')
    
    relatedThemes = []
    for theme in lesson.published_themes().all():
        relatedThemes.append((theme.theme, theme.theme.published_lessons().exclude(lessonPlan=lesson)))
    
    return render(request, 'exhibits/lessonPlanView.html', {'lessonPlan': lesson, 'q': '', 'exhibitItems': exhibitItems, 'relatedThemes': relatedThemes})

@cache_by_session_state
def exhibitItemView(request):
    response = {'exhibits': []}
    exhibits = Exhibit.objects.all()
    for exhibit in exhibits:
        items = []
        exhibit_items = exhibit.exhibititem_set(manager='all_objects').all().order_by('order')
        for exhibit_item in exhibit_items:
            items.append({
                'item_id': exhibit_item.item_id,
                'custom_crop': bool(exhibit_item.custom_crop),
                'custom_metadata': exhibit_item.custom_metadata,
                'custom_title': exhibit_item.custom_title,
                'published': exhibit_item.publish})
        response['exhibits'].append({
            'title': exhibit.title, 
            'url': reverse('exhibits:exhibitView', kwargs={
                'exhibit_id': exhibit.id, 
                'exhibit_slug': exhibit.slug}),
            'id': exhibit.id,
            'items': items})

    essays = HistoricalEssay.objects.all()
    for essay in essays:
        items = []
        exhibit_items = essay.exhibititem_set(manager='all_objects').all().order_by('order')
        for exhibit_item in exhibit_items:
            items.append({
                'item_id': exhibit_item.item_id,
                'custom_crop': bool(exhibit_item.custom_crop),
                'custom_metadata': exhibit_item.custom_metadata,
                'custom_title': exhibit_item.custom_title,
                'published': exhibit_item.publish})
        response['exhibits'].append({
            'title': essay.title, 
            'url': reverse('exhibits:essayView', kwargs={
                'essay_id': essay.id, 
                'essay_slug': essay.slug}),
            'id': essay.id,
            'items': items})

    lessons = LessonPlan.objects.all()
    for lesson in lessons:
        items = []
        exhibit_items = lesson.exhibititem_set(manager='all_objects').all().order_by('order')
        for exhibit_item in exhibit_items:
            items.append({
                'item_id': exhibit_item.item_id,
                'custom_crop': bool(exhibit_item.custom_crop),
                'custom_metadata': exhibit_item.custom_metadata,
                'custom_title': exhibit_item.custom_title,
                'published': exhibit_item.publish})
        response['exhibits'].append({
            'title': lesson.title, 
            'url': reverse('for-teachers:lessonPlanView', kwargs={
                'lesson_id': lesson.id, 
                'lesson_slug': lesson.slug}),
            'id': lesson.id,
            'items': items})

    return JsonResponse(response)

@cache_by_session_state
def item_health(request): 
    page_size = 100
    exhibit_item_ids = ExhibitItem.objects.values_list('item_id', flat=True)
    missing_items = []
    for start in range(0, len(exhibit_item_ids), page_size):
        page = exhibit_item_ids[start:start+page_size]
        solr_list = SOLR_get_list(page)
        if solr_list.numFound == page_size:
            continue
        else:
            solr_ids = [item['id'] for item in solr_list.results]
            missing = list((set(page) - set(solr_ids)))
            missing_items = missing_items + missing

    published_missing = []
    unpublished_missing = []

    published_missing_link = []
    unpublished_missing_link = []

    published_investigate = []
    unpublished_investigate = []

    # .exclude(publish=False).exclude(exhibit__publish=False)

    for item_id in missing_items:
        missing_items_by_id = ExhibitItem.objects.filter(item_id=item_id)
        for missing_item in missing_items_by_id:
            # if NO custom data - this is definitely a problem object
            if (not missing_item.custom_crop 
                and not missing_item.custom_link 
                and not missing_item.custom_metadata 
                and not missing_item.custom_title):
                if (missing_item.publish == True 
                    and ((
                        missing_item.exhibit and missing_item.exhibit.publish==True)
                        or (missing_item.lesson_plan and missing_item.lesson_plan.publish==True)
                        or (missing_item.historical_essay and missing_item.historical_essay.publish==True)
                        )):
                    published_missing.append(missing_item)
                else:
                    unpublished_missing.append(missing_item)

            # if ALL custom data - this is definitely not a problem object
            elif (missing_item.custom_crop 
                and missing_item.custom_link
                and missing_item.custom_metadata
                and missing_item.custom_title):
                continue

            # has some, but not all custom data, definitely missing custom link
            elif (missing_item.custom_crop
                and not missing_item.custom_link
                and missing_item.custom_metadata
                and missing_item.custom_title):
                if (missing_item.publish == True 
                    and ((
                        missing_item.exhibit and missing_item.exhibit.publish==True)
                        or (missing_item.lesson_plan and missing_item.lesson_plan.publish==True)
                        or (missing_item.historical_essay and missing_item.historical_essay.publish==True)
                        )):
                    published_missing_link.append(missing_item)
                else:
                    unpublished_missing_link.append(missing_item)
            else:
                if (missing_item.publish == True 
                    and ((
                        missing_item.exhibit and missing_item.exhibit.publish==True)
                        or (missing_item.lesson_plan and missing_item.lesson_plan.publish==True)
                        or (missing_item.historical_essay and missing_item.historical_essay.publish==True)
                        )):
                    published_investigate.append(missing_item)
                else:
                    unpublished_investigate.append(missing_item)

    # print(f"RED: {has_no_custom}")
    # print(len(has_no_custom))
    # print(f"ORANGE - MISSING CUSTOM SOMETHING: {has_some_custom}")
    # print(len(has_some_custom))

    # custom_crop = ExhibitItem.objects.exclude(custom_crop='')
    # custom_link = ExhibitItem.objects.exclude(custom_link='')
    # custom_metadata = ExhibitItem.objects.exclude(custom_metadata='')
    # custom_title = ExhibitItem.objects.exclude(custom_title='')

    context = {
        # 'custom_crop_count': len(custom_crop),
        # 'custom_link_count': len(custom_link),
        # 'custom_metadata_count': len(custom_metadata),
        # 'custom_title_count': len(custom_title),
        # 'exhibit_item_count': ExhibitItem.objects.count(),
        'published_missing': published_missing,
        'unpublished_missing': unpublished_missing,
        'published_missing_link': published_missing_link,
        'unpublished_missing_link': unpublished_missing_link,
        'published_investigate': published_investigate,
        'unpublished_investigate': unpublished_investigate
    }

    return render(request, 'exhibits/item_health.html', context)



