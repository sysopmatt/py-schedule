from django.contrib import admin

from .models import Schedule


# admin.site.register(Schedule)
@admin.register(Schedule)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("title", "day")
    ordering = ("show", "day")
