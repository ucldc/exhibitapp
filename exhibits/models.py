

from builtins import object
import os.path
import re
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils.encoding import python_2_unicode_compatible
from django.conf import settings
from exhibits.custom_fields import HeroField
from exhibits.md5s3stash import md5s3stash

try:
    from calisphere.cache_retry import SOLR_get
    from calisphere.es_cache_retry import es_get
except ImportError:
    from exhibits.cache_retry import SOLR_get
    # from exhibits.es_cache_retry import es_get

RENDERING_OPTIONS = (
    ('H', 'HTML'),
    ('T', 'Plain Text'),
    ('M', 'Markdown')
)

def getCollectionData(collection_data):
    collection = {}
    parts = collection_data.split('::')
    collection['url'] = parts[0] if len(parts) >= 1 else ''
    collection['name'] = parts[1] if len(parts) >= 2 else ''
    collection_api_url = re.match(
        r'^https://registry\.cdlib\.org/api/v1/collection/(?P<url>\d*)/?',
        collection['url'])
    if collection_api_url is None:
        print('no collection api url:')
        collection['id'] = ''
    else:
        collection['id'] = collection_api_url.group('url')

        collection['local_id'] = ''
        collection['slug'] = ''

    return collection

def getRepositoryData(repository_data):
    repository = {}
    parts = repository_data.split('::')
    repository['url'] = parts[0] if len(parts) >= 1 else ''
    repository['name'] = parts[1] if len(parts) >= 2 else ''
    repository['campus'] = parts[2] if len(parts) >= 3 else ''

    repository_api_url = re.match(
        r'^https://registry\.cdlib\.org/api/v1/repository/(?P<url>\d*)/',
        repository['url'])
    if repository_api_url is None:
        print('no repository api url')
        repository['id'] = ''
    else:
        repository['id'] = repository_api_url.group('url')
        # repository_details = app.registry.repository_data.get(
        #     int(repository['id']), {})

        repository['ga_code'] = ''

    return repository

def get_reference_image_md5(item_id):
    item_id_search_term = 'id:"{0}"'.format(item_id)
    item_search = es_get(item_id)

    if item_search and 'reference_image_md5' in item_search.item:
        return item_search.item['reference_image_md5']
    else:
        return None

# class ImageArk(models.Model):
#     hero = models.ImageField(blank=True, verbose_name='Hero Image', upload_to='uploads/')
#     lockup_derivative = models.ImageField(blank=True, verbose_name='Lockup Image', upload_to='uploads/')
#     alternate_lockup_derivative = models.ImageField(blank=True, verbose_name='Alternate Lockup Image', upload_to='uploads/')
#     item_id = models.CharField(blank=True, max_length=200)
#
#     def __str__(self):
#         return self.item_id

class PublishedExhibitManager(models.Manager):
    def get_queryset(self):
        if settings.EXHIBIT_PREVIEW:
            return super(PublishedExhibitManager, self).get_queryset()
        else:
            return super(PublishedExhibitManager, self).get_queryset().filter(publish=True)

@python_2_unicode_compatible
class Exhibit(models.Model):
    title = models.CharField(max_length=512)
    slug = models.SlugField(max_length=255, unique=True)
    short_title = models.CharField(max_length=255, blank=True)
    blockquote = models.CharField(max_length=512, blank=True)     #default for blockquote is first sentence of essay
    byline = models.TextField(blank=True, verbose_name="Credits", help_text="Curator name(s) and titles, Any other collaborators, Institutional affiliation, Date of publication")
    byline_render_as = models.CharField(max_length=1, choices=RENDERING_OPTIONS, default='H', verbose_name="Render credits as")
    curator = models.TextField()
    copyright_year = models.IntegerField()
    copyright_holder = models.TextField()
    overview = models.TextField(verbose_name='Exhibit Overview', blank=True)
    render_as = models.CharField(max_length=1, choices=RENDERING_OPTIONS, default='H')
    citations = models.TextField(blank=True, verbose_name="Citations/References")
    citations_render_as = models.CharField(max_length=1, choices=RENDERING_OPTIONS, default='H', verbose_name="Render citations as")

    publish = models.BooleanField(verbose_name='Ready for publication?', default=False)
    color = models.CharField(max_length=20, blank=True)
    scraped_from = models.CharField(max_length=250, blank=True)

    hero = models.ImageField(blank=True, verbose_name='Hero Image', upload_to='uploads/', null=True)
    lockup_derivative = models.ImageField(blank=True, null=True, verbose_name='Lockup Image', upload_to='uploads/')
    alternate_lockup_derivative = models.ImageField(blank=True, null=True, verbose_name='Alternate Lockup Image', upload_to='uploads/')
    item_id = models.CharField(blank=True, max_length=200)
    hero_first = models.BooleanField(verbose_name='Use hero for lockups?', default=False)

    meta_description = models.CharField(max_length=255, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)

    objects = PublishedExhibitManager()

    def __str__(self):
        return self.title

    def published_themes(self):
        if settings.EXHIBIT_PREVIEW:
            return self.exhibittheme_set
        else:
            return self.exhibittheme_set.filter(theme__publish=True)

    def published_essays(self):
        if settings.EXHIBIT_PREVIEW:
            return self.historicalessayexhibit_set
        else:
            return self.historicalessayexhibit_set.filter(historicalEssay__publish=True)

    def published_lessons(self):
        if settings.EXHIBIT_PREVIEW:
            return self.lessonplanexhibit_set
        else:
            return self.lessonplanexhibit_set.filter(lessonPlan__publish=True)

    def get_absolute_url(self):
        return reverse('exhibits:exhibitView', kwargs={'exhibit_id': self.id, 'exhibit_slug': self.slug})

    def exhibit_lockup(self):
        if self.lockup_derivative:
            return settings.THUMBNAIL_URL + "crop/273x182/" + self.lockup_derivative.name
        elif self.hero_first:
            return settings.THUMBNAIL_URL + "crop/273x182/" + self.hero.name
        else:
            reference_image_md5 = get_reference_image_md5(self.item_id)
            if reference_image_md5:
                return settings.THUMBNAIL_URL + "crop/273x182/" + reference_image_md5
            elif self.hero:
                return settings.THUMBNAIL_URL + "crop/273x182/" + self.hero.name
            else:
                return None

    def exhibit_lockup_sm(self):
        if self.hero_first:
            return settings.THUMBNAIL_URL + "crop/298x121/" + self.hero.name
        else:
            reference_image_md5 = get_reference_image_md5(self.item_id)
            if reference_image_md5:
               return settings.THUMBNAIL_URL + "crop/298x121/" +  reference_image_md5
            elif self.hero:
                return settings.THUMBNAIL_URL + "crop/298x121/" + self.hero.name
            else:
                return None

    def social_media_card(self):
        if self.item_id:
            reference_image_md5 = get_reference_image_md5(self.item_id)
            if reference_image_md5:
               return settings.THUMBNAIL_URL + "clip/999x999/" +  reference_image_md5
            elif self.hero:
                return settings.THUMBNAIL_URL + "clip/999x999/" + self.hero.name
            else:
                return None
        else:
            return settings.THUMBNAIL_URL + "clip/999x999/" + self.hero.name

    push_to_s3 = ['hero', 'lockup_derivative', 'alternate_lockup_derivative']
    def save(self, *args, **kwargs):
        super(Exhibit, self).save(*args, **kwargs)
        for s3field in self.push_to_s3:
            name = getattr(self, s3field).name
            if name:
                url = settings.MEDIA_ROOT + "/" + name
                if os.path.isfile(url):
                    field_instance = getattr(self, s3field)
                    report = md5s3stash(url, settings.S3_STASH, settings.S3_ID)
                    field_instance.storage.delete(name)
                    field_instance.name = report.md5
                    upload_to = self._meta.get_field(s3field).upload_to
                    self._meta.get_field(s3field).upload_to = ''
                    super(Exhibit, self).save(update_fields=[s3field])
                    self._meta.get_field(s3field).upload_to = upload_to


class PublishedHistoricalEssayManager(models.Manager):
    def get_queryset(self):
        if settings.EXHIBIT_PREVIEW:
            return super(PublishedHistoricalEssayManager, self).get_queryset()
        else:
            return super(PublishedHistoricalEssayManager, self).get_queryset().filter(publish=True)

@python_2_unicode_compatible
class HistoricalEssay(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=255, unique=True)

    hero = models.ImageField(blank=True, verbose_name='Hero Image', upload_to='uploads/', null=True)
    lockup_derivative = models.ImageField(blank=True, null=True, verbose_name='Lockup Image', upload_to='uploads/')
    alternate_lockup_derivative = models.ImageField(blank=True, null=True, verbose_name='Alternate Lockup Image', upload_to='uploads/')
    item_id = models.CharField(blank=True, max_length=200)
    hero_first = models.BooleanField(verbose_name='Use hero for lockups?', default=False)

    blockquote = models.CharField(max_length=200, blank=True)
    essay = models.TextField(blank=True)
    render_as = models.CharField(max_length=1, choices=RENDERING_OPTIONS, default='H')

    byline = models.TextField(blank=True, verbose_name="Credits", help_text="Curator name(s) and titles, Any other collaborators, Institutional affiliation, Date of publication")
    byline_render_as = models.CharField(max_length=1, choices=RENDERING_OPTIONS, default='H', verbose_name="Render credits as")
    curator = models.TextField()
    copyright_year = models.IntegerField()
    copyright_holder = models.TextField()

    go_further = models.TextField(blank=True)
    go_further_render_as = models.CharField(max_length=1, choices=RENDERING_OPTIONS, default='H', verbose_name='Render as')

    publish = models.BooleanField(verbose_name='Ready for publication?', default=False)
    color = models.CharField(max_length=20, blank=True, help_text="Please provide color in <code>#xxx</code>, <code>#xxxxxx</code>, <code>rgb(xxx,xxx,xxx)</code>, or <code>rgba(xxx,xxx,xxx,x.x)</code> formats.")
    meta_description = models.CharField(max_length=255, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)

    objects = PublishedHistoricalEssayManager()

    def published_exhibits(self):
        if settings.EXHIBIT_PREVIEW:
            return self.historicalessayexhibit_set
        else:
            return self.historicalessayexhibit_set.filter(exhibit__publish=True)

    def published_themes(self):
        if settings.EXHIBIT_PREVIEW:
            return self.historicalessaytheme_set
        else:
            return self.historicalessaytheme_set.filter(theme__publish=True)

    def get_absolute_url(self):
        return reverse('exhibits:essayView', kwargs={'essay_id': self.id, 'essay_slug': self.slug})

    push_to_s3 = ['hero', 'lockup_derivative', 'alternate_lockup_derivative']
    def save(self, *args, **kwargs):
        super(HistoricalEssay, self).save(*args, **kwargs)
        for s3field in self.push_to_s3:
            name = getattr(self, s3field).name
            if name:
                url = settings.MEDIA_ROOT + "/" + name
                if os.path.isfile(url):
                    field_instance = getattr(self, s3field)
                    report = md5s3stash(url, settings.S3_STASH, settings.S3_ID)
                    field_instance.storage.delete(name)
                    field_instance.name = report.md5
                    upload_to = self._meta.get_field(s3field).upload_to
                    self._meta.get_field(s3field).upload_to = ''
                    super(HistoricalEssay, self).save(update_fields=[s3field])
                    self._meta.get_field(s3field).upload_to = upload_to

    def lockup(self):
        if self.hero_first:
            return settings.THUMBNAIL_URL + "crop/298x121/" + self.hero.name
        else:
            reference_image_md5 = get_reference_image_md5(self.item_id)
            if reference_image_md5:
               return settings.THUMBNAIL_URL + "crop/298x121/" +  reference_image_md5
            elif self.hero:
                return settings.THUMBNAIL_URL + "crop/298x121/" + self.hero.name
            else:
                return None

    def social_media_card(self):
        if self.item_id:
            reference_image_md5 = get_reference_image_md5(self.item_id)
            if reference_image_md5:
               return settings.THUMBNAIL_URL + "clip/999x999/" +  reference_image_md5
            elif self.hero:
                return settings.THUMBNAIL_URL + "clip/999x999/" + self.hero.name
            else:
                return None
        else:
            return settings.THUMBNAIL_URL + "clip/999x999/" + self.hero.name

    def __str__(self):
        return self.title


class PublishedLessonPlanManager(models.Manager):
    def get_queryset(self):
        if settings.EXHIBIT_PREVIEW:
            return super(PublishedLessonPlanManager, self).get_queryset()
        else:
            return super(PublishedLessonPlanManager, self).get_queryset().filter(publish=True)

@python_2_unicode_compatible
class LessonPlan(models.Model):
    title = models.CharField(max_length=200)
    sub_title = models.CharField(max_length=512, blank=True)
    slug = models.SlugField(max_length=255, unique=True)

    lockup_derivative = models.ImageField(blank=True, null=True, verbose_name='Lockup Image', upload_to='uploads/')
    item_id = models.CharField(blank=True, max_length=200)

    overview = models.TextField(blank=True)
    render_as = models.CharField(max_length=1, choices=RENDERING_OPTIONS, default='H')
    lesson_plan = models.CharField(max_length=255, blank=True, verbose_name='Lesson Plan File URL')
    # lesson_plan = models.FileField(blank=True, verbose_name='Lesson Plan File', upload_to='uploads/')
    grade_level = models.CharField(max_length=200, blank=True)
    byline = models.TextField(blank=True, verbose_name="Credits", help_text="Curator name(s) and titles, Any other collaborators, Institutional affiliation, Date of publication")
    byline_render_as = models.CharField(max_length=1, choices=RENDERING_OPTIONS, default='H', verbose_name="Render credits as")
    curator = models.TextField()
    copyright_year = models.IntegerField()
    copyright_holder = models.TextField()

    publish = models.BooleanField(verbose_name='Ready for publication?', default=False)
    meta_description = models.CharField(max_length=255, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)

    objects = PublishedLessonPlanManager()

    def __str__(self):
        return self.title

    def published_themes(self):
        if settings.EXHIBIT_PREVIEW:
            return self.lessonplantheme_set
        else:
            return self.lessonplantheme_set.filter(theme__publish=True)

    def published_exhibits(self):
        if settings.EXHIBIT_PREVIEW:
            return self.lessonplanexhibit_set
        else:
            return self.lessonplanexhibit_set.filter(exhibit__publish=True)

    def get_absolute_url(self):
        return reverse('for-teachers:lessonPlanView', kwargs={'lesson_id': self.id, 'lesson_slug': self.slug})

    def lockup(self):
        if self.lockup_derivative:
            return settings.THUMBNAIL_URL + "crop/298x121/" + self.lockup_derivative.name
        else:
            reference_image_md5 = get_reference_image_md5(self.item_id)
            if reference_image_md5:
               return settings.THUMBNAIL_URL + "crop/298x121/" +  reference_image_md5
            else:
                return None

    def social_media_card(self):
        if self.lockup_derivative:
            return settings.THUMBNAIL_URL + "clip/999x999/" + self.lockup_derivative.name
        else:
            reference_image_md5 = get_reference_image_md5(self.item_id)
            if reference_image_md5:
               return settings.THUMBNAIL_URL + "clip/999x999/" +  reference_image_md5
            else:
                return None

    push_to_s3 = ['lockup_derivative']
    def save(self, *args, **kwargs):
        super(LessonPlan, self).save(*args, **kwargs)
        for s3field in self.push_to_s3:
            name = getattr(self, s3field).name
            if name:
                url = settings.MEDIA_ROOT + "/" + name
                if os.path.isfile(url):
                    field_instance = getattr(self, s3field)
                    report = md5s3stash(url, settings.S3_STASH, settings.S3_ID)
                    field_instance.storage.delete(name)
                    field_instance.name = report.md5
                    upload_to = self._meta.get_field(s3field).upload_to
                    self._meta.get_field(s3field).upload_to = ''
                    super(LessonPlan, self).save(update_fields=[s3field])
                    self._meta.get_field(s3field).upload_to = upload_to


class PublishedThemeManager(models.Manager):
    def get_queryset(self):
        if settings.EXHIBIT_PREVIEW:
            return super(PublishedThemeManager, self).get_queryset()
        else:
            return super(PublishedThemeManager, self).get_queryset().filter(publish=True)

@python_2_unicode_compatible
class Theme(models.Model):
    title = models.CharField(max_length=200)
    sort_title = models.CharField(blank=True, max_length=200, verbose_name='Sortable Title')
    slug = models.SlugField(max_length=255, unique=True)
    color = models.CharField(max_length=20, blank=True)
    byline = models.TextField(blank=True, verbose_name="Credits", help_text="Curator name(s) and titles, Any other collaborators, Institutional affiliation, Date of publication")
    byline_render_as = models.CharField(max_length=1, choices=RENDERING_OPTIONS, default='H', verbose_name="Render credits as")
    curator = models.TextField()
    copyright_year = models.IntegerField()
    copyright_holder = models.TextField()
    essay = models.TextField(blank=True, verbose_name='Theme overview')
    render_as = models.CharField(max_length=1, choices=RENDERING_OPTIONS, default='H')

    hero = models.ImageField(blank=True, verbose_name='Hero Image', upload_to='uploads/')
    lockup_derivative = models.ImageField(blank=True, null=True, verbose_name='Lockup Image', upload_to='uploads/')
    alternate_lockup_derivative = models.ImageField(blank=True, null=True, verbose_name='Alternate Lockup Image', upload_to='uploads/')
    item_id = models.CharField(blank=True, max_length=200)
    hero_first = models.BooleanField(verbose_name='Use hero for lockups?', default=False)

    publish = models.BooleanField(verbose_name='Ready for publication?', default=False)
    meta_description = models.CharField(max_length=255, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)

    objects = PublishedThemeManager()

    CALHISTORY = 'cal-history'
    CALCULTURES = 'cal-cultures'
    JARDA = 'jarda'
    CATEGORY_CHOICES = (
        (CALHISTORY, 'California History'),
        (CALCULTURES, 'California Cultures'),
        (JARDA, 'JARDA')
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, blank=True)

    def published_essays(self):
        if settings.EXHIBIT_PREVIEW:
            return self.historicalessaytheme_set
        else:
            return self.historicalessaytheme_set.filter(historicalEssay__publish=True)

    def published_lessons(self):
        if settings.EXHIBIT_PREVIEW:
            return self.lessonplantheme_set
        else:
            return self.lessonplantheme_set.filter(lessonPlan__publish=True)

    def published_exhibits(self):
        if settings.EXHIBIT_PREVIEW:
            return self.exhibittheme_set
        else:
            return self.exhibittheme_set.filter(exhibit__publish=True)

    def get_absolute_url(self):
        return reverse('exhibits:themeView', kwargs={'theme_id': self.id, 'theme_slug': self.slug})

    def theme_lockup(self):
        if self.lockup_derivative:
            return settings.THUMBNAIL_URL + "crop/420x210/" + self.lockup_derivative.name
        elif self.hero_first:
            return settings.THUMBNAIL_URL + "crop/420x210/" + self.hero.name
        else:
            reference_image_md5 = get_reference_image_md5(self.item_id)
            if reference_image_md5:
               return settings.THUMBNAIL_URL + "crop/420x210/" +  reference_image_md5
            elif self.hero:
                return settings.THUMBNAIL_URL + "crop/420x210/" + self.hero.name
            else:
                return None

    push_to_s3 = ['hero', 'lockup_derivative', 'alternate_lockup_derivative']
    def save(self, *args, **kwargs):
        super(Theme, self).save(*args, **kwargs)
        for s3field in self.push_to_s3:
            name = getattr(self, s3field).name
            if name:
                url = settings.MEDIA_ROOT + "/" + name
                if os.path.isfile(url):
                    field_instance = getattr(self, s3field)
                    report = md5s3stash(url, settings.S3_STASH, settings.S3_ID)
                    field_instance.storage.delete(name)
                    field_instance.name = report.md5
                    upload_to = self._meta.get_field(s3field).upload_to
                    self._meta.get_field(s3field).upload_to = ''
                    super(Theme, self).save(update_fields=[s3field])
                    self._meta.get_field(s3field).upload_to = upload_to

    def social_media_card(self):
        if self.item_id:
            reference_image_md5 = get_reference_image_md5(self.item_id)
            if reference_image_md5:
               return settings.THUMBNAIL_URL + "clip/999x999/" +  reference_image_md5
            elif self.hero:
                return settings.THUMBNAIL_URL + "clip/999x999/" + self.hero.name
            else:
                return None
        else:
            return settings.THUMBNAIL_URL + "clip/999x999/" + self.hero.name

    def __str__(self):
        return self.title

class PublishedExhibitItemManager(models.Manager):
    def get_queryset(self):
        if settings.EXHIBIT_PREVIEW:
            return super(PublishedExhibitItemManager, self).get_queryset()
        else:
            return super(PublishedExhibitItemManager, self).get_queryset().filter(publish=True)

@python_2_unicode_compatible
class ExhibitItem(models.Model):
    item_id = models.CharField(max_length=200)

    exhibit = models.ForeignKey(Exhibit, on_delete=models.CASCADE, blank=True, null=True)
    lesson_plan = models.ForeignKey(LessonPlan, on_delete=models.CASCADE, blank=True, null=True)
    historical_essay = models.ForeignKey(HistoricalEssay, on_delete=models.CASCADE, blank=True, null=True)
    order = models.IntegerField(blank=True, null=True)
    lesson_plan_order = models.IntegerField(blank=True, null=True)
    historical_essay_order = models.IntegerField(blank=True, null=True)

    publish = models.BooleanField(verbose_name='Ready for publication?', default=True)

    essay = models.TextField(blank=True, verbose_name='Item-level exhibit information')
    render_as = models.CharField(max_length=1, choices=RENDERING_OPTIONS, default='T')

    custom_crop = models.ImageField(blank=True, null=True, upload_to='uploads/custom_item_crop/')
    custom_metadata = models.TextField(blank=True, verbose_name='Custom metadata')
    metadata_render_as = models.CharField(max_length=1, choices=RENDERING_OPTIONS, default='M')
    custom_link = models.CharField(max_length=512, blank=True)
    custom_title = models.CharField(max_length=512, blank=True)

    citations = models.TextField(blank=True, verbose_name="Citations/References")
    citations_render_as = models.CharField(max_length=1, choices=RENDERING_OPTIONS, default='H', verbose_name="Render citations as")

    #lat/long models
    lat = models.FloatField(default=37.8086906)
    lon = models.FloatField(default=-122.2675416)
    place = models.CharField(max_length=512, blank=True)
    exact = models.BooleanField(default=False)

    objects = PublishedExhibitItemManager()
    all_objects = models.Manager()

    def __str__(self):
        return self.item_id

    def solrData(self):
        item_id_search_term = 'id:"{0}"'.format(self.item_id)
        item_search = es_get(self.item_id)
        if item_search:
            item = item_search.item

            item['parsed_collection_data'] = []
            item['parsed_repository_data'] = []
            for collection_data in item['collection_data']:
                item['parsed_collection_data'].append(getCollectionData(collection_data=collection_data))
            if 'repository_data' in item:
                for repository_data in item['repository_data']:
                    item['parsed_repository_data'].append(getRepositoryData(repository_data=repository_data))

            return item
        else:
            return None

    def imgUrl(self):
        if self.custom_crop:
            return settings.THUMBNAIL_URL + "crop/210x210/" + self.custom_crop.name
        else:
            reference_image_md5 = get_reference_image_md5(self.item_id)
            if reference_image_md5:
               return settings.THUMBNAIL_URL + "crop/210x210/" +  reference_image_md5
            else:
                return None

    push_to_s3 = ['custom_crop']
    def save(self, *args, **kwargs):
        super(ExhibitItem, self).save(*args, **kwargs)
        for s3field in self.push_to_s3:
            name = getattr(self, s3field).name
            if name:
                url = settings.MEDIA_ROOT + "/" + name
                if os.path.isfile(url):
                    field_instance = getattr(self, s3field)
                    report = md5s3stash(url, settings.S3_STASH, settings.S3_ID)
                    field_instance.storage.delete(name)
                    field_instance.name = report.md5
                    upload_to = self._meta.get_field(s3field).upload_to
                    self._meta.get_field(s3field).upload_to = ''
                    super(ExhibitItem, self).save(update_fields=[s3field])
                    self._meta.get_field(s3field).upload_to = upload_to

@python_2_unicode_compatible
class NotesItem(models.Model):
    title = models.CharField(max_length=200)
    exhibit = models.ForeignKey(Exhibit, on_delete=models.CASCADE)
    order = models.IntegerField(blank=True, null=True)
    essay = models.TextField(blank=True, verbose_name='Note')
    render_as = models.CharField(max_length=1, choices=RENDERING_OPTIONS, default='T')

    def __str__(self):
        return self.title

    class Meta(object):
        ordering = ['order']

class HistoricalEssayExhibit(models.Model):
    exhibit = models.ForeignKey(Exhibit, on_delete=models.CASCADE)
    historicalEssay = models.ForeignKey(HistoricalEssay, on_delete=models.CASCADE)
    order = models.IntegerField(blank=True, null=True)

    class Meta(object):
        unique_together = ('exhibit', 'historicalEssay')
        verbose_name = 'Historical Essay'
        ordering = ['order']

class LessonPlanExhibit(models.Model):
    exhibit = models.ForeignKey(Exhibit, on_delete=models.CASCADE)
    lessonPlan = models.ForeignKey(LessonPlan, on_delete=models.CASCADE)
    order = models.IntegerField(blank=True, null=True)

    class Meta(object):
        unique_together = ('exhibit', 'lessonPlan')
        verbose_name = 'Lesson Plan'
        ordering = ['order']

# Exhibits ordered within Themes
@python_2_unicode_compatible
class ExhibitTheme(models.Model):
    exhibit = models.ForeignKey(Exhibit, on_delete=models.CASCADE)
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE)
    order = models.IntegerField(blank=True, null=True)

    class Meta(object):
        unique_together = ('exhibit', 'theme')
        verbose_name = 'Exhibit'

    def __str__(self):
        return self.theme.title + ', ' + self.exhibit.title

class LessonPlanTheme(models.Model):
    lessonPlan = models.ForeignKey(LessonPlan, on_delete=models.CASCADE)
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE)
    order = models.IntegerField(blank=True, null=True)

    class Meta(object):
        unique_together = ('lessonPlan', 'theme')
        verbose_name = 'Lesson Plan'
        ordering = ['order']

class HistoricalEssayTheme(models.Model):
    historicalEssay = models.ForeignKey(HistoricalEssay, on_delete=models.CASCADE)
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE)
    order = models.IntegerField(blank=True, null=True)

    class Meta(object):
        unique_together = ('historicalEssay', 'theme')
        verbose_name = 'Historical Essay'
        ordering = ['order']
