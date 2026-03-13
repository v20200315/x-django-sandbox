from django.contrib import admin

from .models import DI


@admin.register(DI)
class DIAdmin(admin.ModelAdmin):
    list_display = ('value', 'owner', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('value', 'owner__email')
    raw_id_fields = ('owner',)
    readonly_fields = ('id', 'created_at', 'updated_at')
