from django.contrib import admin

from .models import AI, DI, UDIDIPI, UDIDIPIAIValue, UDIDIPIDILink


class UDIDIPIDILinkInline(admin.TabularInline):
    model = UDIDIPIDILink
    extra = 0


class UDIDIPIAIValueInline(admin.TabularInline):
    model = UDIDIPIAIValue
    extra = 0


@admin.register(UDIDIPI)
class UDIDIPIAdmin(admin.ModelAdmin):
    list_display = ('id', 'generated_code', 'owner', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('generated_code', 'owner__email')
    raw_id_fields = ('owner',)
    readonly_fields = ('id', 'generated_code', 'created_at', 'updated_at')
    inlines = [UDIDIPIDILinkInline, UDIDIPIAIValueInline]


@admin.register(AI)
class AIAdmin(admin.ModelAdmin):
    list_display = ('code', 'description', 'format_spec', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('code', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(DI)
class DIAdmin(admin.ModelAdmin):
    list_display = ('value', 'owner', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('value', 'owner__email')
    raw_id_fields = ('owner',)
    readonly_fields = ('id', 'created_at', 'updated_at')
