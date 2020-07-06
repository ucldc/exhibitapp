


from django.contrib import admin
from django.utils.safestring import mark_safe
from django import forms
from django.db import models
from django.urls import reverse

# Register your models here.

from .models import *

class ExhibitItemInline(admin.TabularInline):
    model = ExhibitItem
    classes = ('collapse',)
    fields = ['order', 'publish', 'item_id', 'essay', 'render_as', 'img_display', 'citations', 'citations_render_as', 'link_to_exhibit_item']
    # 'imgUrl', 'custom_crop', 'custom_link', 'custom_title', 'custom_metadata', 'metadata_render_as'
    extra = 0
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'cols': 50, 'rows': 5})}
    }
    readonly_fields = ['img_display', 'link_to_exhibit_item']

    def link_to_exhibit_item(self, instance):
        link = reverse("admin:exhibits_exhibititem_change", args=[instance.id])
        return mark_safe(f"<a href='{link}'>Click to add custom crop, link, title, and metadata</a>")
    link_to_exhibit_item.short_description="Link to Exhibit Item"

    def img_display(self, instance):
        if instance.imgUrl():
            return mark_safe("<img src='" + instance.imgUrl() + "'/>")
        else:
            return None
    img_display.short_description = "Thumbnail"

class LessonPlanItemInline(admin.TabularInline):
    model = ExhibitItem
    classes = ('collapse',)
    fields = ['lesson_plan_order', 'publish', 'item_id', 'essay', 'render_as', 'img_display', 'citations', 'citations_render_as', 'link_to_exhibit_item']
    # 'imgUrl', 'custom_crop', 'custom_link', 'custom_title', 'custom_metadata', 'metadata_render_as'
    extra = 0
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'cols': 50, 'rows': 5})}
    }
    readonly_fields = ['imgUrl', 'img_display', 'link_to_exhibit_item']

    def link_to_exhibit_item(self, instance):
        link = reverse("admin:exhibits_exhibititem_change", args=[instance.id])
        return mark_safe(f"<a href='{link}'>Click to add custom crop, link, title, and metadata</a>")
    link_to_exhibit_item.short_description="Link to Lesson Plan Item"

    def img_display(self, instance):
        if instance.imgUrl():
            return mark_safe("<img src='" + instance.imgUrl() + "'/>")
        else:
            return None
    img_display.short_description = "Thumbnail"

class HistoricalEssayItemInline(admin.TabularInline):
    model = ExhibitItem
    classes = ('collapse',)
    fields = ['historical_essay_order', 'publish', 'item_id', 'essay', 'render_as', 'img_display', 'citations', 'citations_render_as', 'link_to_exhibit_item']
    # 'imgUrl', 'custom_crop', 'custom_link', 'custom_title', 'custom_metadata', 'metadata_render_as'
    extra = 0
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'cols': 50, 'rows': 5})}
    }
    readonly_fields = ['imgUrl', 'img_display', 'link_to_exhibit_item']

    def link_to_exhibit_item(self, instance):
        link = reverse("admin:exhibits_exhibititem_change", args=[instance.id])
        return mark_safe(f"<a href='{link}'>Click to add custom crop, link, title, and metadata</a>")
    link_to_exhibit_item.short_description="Link to Historical Essay Item"

    def img_display(self, instance):
        if instance.imgUrl():
            return mark_safe("<img src='" + instance.imgUrl() + "'/>")
        else:
            return None
    img_display.short_description = "Thumbnail"

class NotesItemInline(admin.TabularInline):
    model = NotesItem
    classes = ('collapse',)
    fields = ['order', 'title', 'render_as', 'essay']
    verbose_name = 'Note'
    extra = 0

class HistoricalEssayExhibitInline(admin.TabularInline):
    model = HistoricalEssayExhibit
    classes = ('collapse',)
    fields = ['order', 'historicalEssay']
    extra = 0

class LessonPlanExhibitInline(admin.TabularInline):
    model = LessonPlanExhibit
    classes = ('collapse',)
    fields = ['order', 'lessonPlan']
    extra = 0

class ThemeExhibitInline(admin.TabularInline):
    model = ExhibitTheme
    classes = ('collapse',)
    fields = ['theme']
    verbose_name = 'Theme'
    extra = 0

class ExhibitThemeInline(admin.TabularInline):
    model = ExhibitTheme
    classes = ('collapse',)
    fields = ['order', 'exhibit']
    extra = 0

class HistoricalEssayThemeInline(admin.TabularInline):
    model = HistoricalEssayTheme
    classes = ('collapse',)
    fields = ['order', 'historicalEssay']
    extra = 0

class LessonPlanThemeInline(admin.TabularInline):
    model = LessonPlanTheme
    classes = ('collapse',)
    fields = ['order', 'lessonPlan']
    extra = 0

class HistoricalEssayAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,                      {'fields': [('title', 'slug'), ('blockquote')]}),
        ('Hero Image and Lockup',   {'fields': [('hero', 'lockup_derivative'), ('item_id', 'alternate_lockup_derivative'), ('hero_first')]}),
        ('Publish',                 {'fields': [('color', 'publish')]}),
        ('Essay',                   {'fields': [('essay', 'render_as'), ('go_further', 'go_further_render_as')], 'description': 'Use <code>&lt;h2&gt;</code> as the highest level heading for essays. Use <code>&lt;h4&gt;</code> for headings in Go Further.'}),
        ('About this Essay',        {'fields': [('byline', 'byline_render_as'), ('curator', 'copyright_holder'), ('copyright_year', 'credits_display')], 'classes': ['collapse']}),
        ('Metadata',                {'fields': [('meta_description', 'meta_keywords')], 'classes': ['collapse']})
    ]
    list_display = ('title', 'hero', 'hero_first', 'slug', 'get_absolute_url', 'publish')
    prepopulated_fields = {'slug': ['title']}
    inlines = [HistoricalEssayItemInline]
    readonly_fields = ['credits_display']
    def credits_display(self, instance):
        if instance.curator or instance.copyright_year or instance.copyright_holder:
            return mark_safe(
                """<p>The text of this essay is available under a 
                <a href='https://creativecommons.org/licenses/by/4.0/'>Creative Commons 
                CC-BY license</a>. You are free to share and adapt it however you like, provided you 
                provide attribution as follows:</p><p>{0} curated by {1}, availabled under 
                a <a href="<a href='https://creativecommons.org/licenses/by/4.0/'>">CC BY 4.0 license</a>. 
                \u00A9 {2}, {3}.</p><p>Please note that this license applies 
                only to the descriptive copy and does not apply to any and all digital 
                items that may appear.</p>""".encode('utf-8').format(instance.title, instance.curator, 
                    instance.copyright_year, instance.copyright_holder)
                )
        else:
            return None
    credits_display.short_description = "Credits preview"

class ExhibitAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,                      {'fields': [('title', 'slug'), ('short_title', 'blockquote')]}),
        ('Hero Image and Lockup',   {'fields': [('hero', 'lockup_derivative'), ('item_id', 'alternate_lockup_derivative'), ('hero_first')], 'classes': ['collapse']}),
        ('Publish',                 {'fields': [('color', 'publish'), ('scraped_from')], 'classes': ['collapse']}),
        ('Exhibit Overview',        {'fields': [('overview', 'render_as')], 'classes': ['collapse']}),
        ('About this Exhibit',      {'fields': [('byline', 'byline_render_as'), ('curator', 'copyright_holder'), ('copyright_year', 'credits_display')]}),
        ('Citations/References',    {'fields': [('citations', 'citations_render_as')]}),
        ('Metadata',                {'fields': [('meta_description', 'meta_keywords')], 'classes': ['collapse']})
    ]
    inlines = [ExhibitItemInline, NotesItemInline, ThemeExhibitInline, HistoricalEssayExhibitInline, LessonPlanExhibitInline]
    list_display = ('title', 'hero', 'hero_first', 'slug', 'get_absolute_url', 'publish')
    prepopulated_fields = {'slug': ['title']}
    readonly_fields = ['credits_display']
    def credits_display(self, instance):
        if instance.curator or instance.copyright_year or instance.copyright_holder:
            return mark_safe(
                """<p>The text of this exhibition is available under a 
                <a href='https://creativecommons.org/licenses/by/4.0/'>Creative Commons 
                CC-BY license</a>. You are free to share and adapt it however you like, provided you 
                provide attribution as follows:</p><p>{0} curated by {1}, availabled under 
                a <a href="<a href='https://creativecommons.org/licenses/by/4.0/'>">CC BY 4.0 license</a>. 
                \u00A9 {2}, {3}.</p><p>Please note that this license applies 
                only to the descriptive copy and does not apply to any and all digital 
                items that may appear.</p>""".encode('utf-8').format(instance.title, instance.curator, 
                    instance.copyright_year, instance.copyright_holder)
                )
        else:
            return None
    credits_display.short_description = "Credits preview"

class LessonPlanAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,                      {'fields': [('title', 'slug'), ('sub_title')]}),
        ('Lockup Image and Publish',{'fields': [('lockup_derivative', 'item_id'), ('publish')]}),
        ('Lesson Plan Overview',    {'fields': [('overview', 'render_as'), ('lesson_plan', 'grade_level')]}),
        ('About this Lesson Plan',  {'fields': [('byline', 'byline_render_as'), ('curator', 'copyright_holder'), ('copyright_year', 'credits_display')], 'classes': ['collapse']}),
        ('Metadata',                {'fields': [('meta_description', 'meta_keywords')], 'classes': ['collapse']})
    ]
    prepopulated_fields = {'slug': ['title']}
    list_display = ('title', 'slug', 'get_absolute_url', 'publish')
    inlines = [LessonPlanItemInline]
    readonly_fields = ['credits_display']
    def credits_display(self, instance):
        if instance.curator or instance.copyright_year or instance.copyright_holder:
            return mark_safe(
                """<p>The text of this lesson plan is available under a 
                <a href='https://creativecommons.org/licenses/by/4.0/'>Creative Commons 
                CC-BY license</a>. You are free to share and adapt it however you like, provided you 
                provide attribution as follows:</p><p>{0} curated by {1}, availabled under 
                a <a href="<a href='https://creativecommons.org/licenses/by/4.0/'>">CC BY 4.0 license</a>. 
                \u00A9 {2}, {3}.</p><p>Please note that this license applies 
                only to the descriptive copy and does not apply to any and all digital 
                items that may appear.</p>""".encode('utf-8').format(instance.title, instance.curator, 
                    instance.copyright_year, instance.copyright_holder)
                )
        else:
            return None
    credits_display.short_description = "Credits preview"

class ThemeAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,                      {'fields': [('title', 'slug'), ('sort_title')]}),
        ('Hero Image and Lockup',   {'fields': [('hero', 'lockup_derivative'), ('item_id', 'alternate_lockup_derivative'), ('hero_first')]}),
        ('Publish',                 {'fields': [('color', 'publish'), ('category')]}),
        ('Theme Overview',          {'fields': [('essay', 'render_as')]}),
        ('About this Theme',        {'fields': [('byline', 'byline_render_as'), ('curator', 'copyright_holder'), ('copyright_year', 'credits_display')], 'classes': ['collapse']}),
        ('Metadata',                {'fields': [('meta_description', 'meta_keywords')], 'classes': ['collapse']})
    ]
    inlines = [ExhibitThemeInline, HistoricalEssayThemeInline, LessonPlanThemeInline]
    list_display = ('title', 'hero', 'hero_first', 'slug', 'get_absolute_url', 'publish')
    prepopulated_fields = {'slug': ['title']}
    readonly_fields = ['credits_display']
    def credits_display(self, instance):
        if instance.curator or instance.copyright_year or instance.copyright_holder:
            return mark_safe(
                """<p>The text of this theme is available under a 
                <a href='https://creativecommons.org/licenses/by/4.0/'>Creative Commons 
                CC-BY license</a>. You are free to share and adapt it however you like, provided you 
                provide attribution as follows:</p><p>{0} curated by {1}, availabled under 
                a <a href="<a href='https://creativecommons.org/licenses/by/4.0/'>">CC BY 4.0 license</a>. 
                \u00A9 {2}, {3}.</p><p>Please note that this license applies 
                only to the descriptive copy and does not apply to any and all digital 
                items that may appear.</p>""".encode('utf-8').format(instance.title, instance.curator, 
                    instance.copyright_year, instance.copyright_holder)
                )
        else:
            return None
    credits_display.short_description = "Credits preview"

class ExhibitItemAdmin(admin.ModelAdmin):
    list_display = ('item_id', 'exhibit', 'order', 'lesson_plan', 'lesson_plan_order', 'historical_essay', 'historical_essay_order')
    fieldsets = [
        (None,                      {'fields': [('item_id', 'publish'), ('img_display'), ('container_type', 'container'), ('container_order')]}),
        ('Exhibit Context',         {'fields': [('essay', 'render_as')], 'classes': ['collapse']}),
        ('Citations',               {'fields': [('citations', 'citations_render_as')], 'classes': ['collapse']}),
        ('Custom Data',             {'fields': [('custom_title'), ('custom_crop'), ('custom_metadata', 'metadata_render_as'), ('custom_link')]}),
        ('Migrated Data',           {'fields': [('lat', 'lon'), ('place', 'exact')], 'classes': ['collapse']}),
        (None,                      {'fields': [('return_to_container')]})
    ]

    readonly_fields = ['container_type', 'container', 'container_order', 'img_display', 'return_to_container']

    def img_display(self, instance):
        if instance.imgUrl():
            return mark_safe("<img src='" + instance.imgUrl() + "'/>")
        else:
            return None
    img_display.short_description = "Thumbnail"

    def container_type(self, instance):
        if instance.exhibit:
            return "Exhibit"
        elif instance.historical_essay:
            return "Historical Essay"
        elif instance.lesson_plan:
            return "Lesson Plan"
        else:
            return "Orphaned"
    container_type.short_description = 'Part of'

    def container(self, instance):
        if instance.exhibit:
            link = reverse("admin:exhibits_exhibit_change", args=[instance.exhibit.id])
            return mark_safe(f"{instance.exhibit} <br/><a href='{link}'>Edit this exhibit</a>")
        elif instance.historical_essay:
            link = reverse("admin:exhibits_historicalessay_change", args=[instance.historical_essay.id])
            return mark_safe(f"<b>Historical Essay</b>: {instance.historical_essay} <br/><a href='{link}'>Edit this historical essay</a>")
        elif instance.lesson_plan:
            link = reverse("admin:exhibits_lessonplan_change", args=[instance.lesson_plan.id])
            return mark_safe(f"<b>Lesson Plan</b>: {instance.lesson_plan}<br/><a href='{link}'>Edit this lesson plan</a>")
        else:
            return 'Orphaned exhibit item'
    container.short_description=''

    def container_order(self, instance):
        if instance.exhibit:
            return instance.order
        elif instance.historical_essay:
            return instance.historical_essay_order
        elif instance.lesson_plan:
            return instance.lesson_plan_order
        else:
            return ''
    container_order.short_description='Order'

    def return_to_container(self, instance):
        link = ''
        container_name = ''
        if instance.exhibit:
            link = reverse("admin:exhibits_exhibit_change", args=[instance.exhibit.id])
            container_name = instance.exhibit
        elif instance.historical_essay:
            link = reverse("admin:exhibits_historicalessay_change", args=[instance.historical_essay.id])
            container_name = instance.historical_essay
        elif instance.lesson_plan:
            link = reverse("admin:exhibits_lessonplan_change", args=[instance.lesson_plan.id])
            container_name = instance.lesson_plan
        return mark_safe(f"Please click 'save and continue editing' below and then click here to return to <a href='{link}'>Edit {container_name}</a>")
    return_to_container.short_description='Help text'

admin.site.register(ExhibitItem, ExhibitItemAdmin)
admin.site.register(Exhibit, ExhibitAdmin)
admin.site.register(Theme, ThemeAdmin)
admin.site.register(HistoricalEssay, HistoricalEssayAdmin)
admin.site.register(LessonPlan, LessonPlanAdmin)
