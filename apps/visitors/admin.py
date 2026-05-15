from django.contrib import admin
from .models import Visitor, Visit

@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'document_id', 'visitor_type')
    search_fields = ('document_id', 'last_name')

@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ('visitor', 'person_to_visit', 'entry_time', 'status')
    list_filter = ('status', 'entry_time')