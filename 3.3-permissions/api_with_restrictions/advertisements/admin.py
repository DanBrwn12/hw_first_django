from django.contrib import admin
from advertisements.models import Advertisement, Favorite


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description', 'creator__username')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('status',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'advertisement', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'advertisement__title')
    readonly_fields = ('created_at',)
