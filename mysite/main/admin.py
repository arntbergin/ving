from django.contrib import admin
from django.contrib import messages
from .models import PrisAbonnement
from .utils import sjekk_abonnementer
from .models import VingURL





@admin.register(VingURL)
class VingURLAdmin(admin.ModelAdmin):
    list_display = ('navn', 'url', 'aktiv', 'opprettet')
    list_filter = ('aktiv',)
    search_fields = ('navn', 'url')


@admin.register(PrisAbonnement)
class PrisAbonnementAdmin(admin.ModelAdmin):
    list_display = ('bruker', 'destinasjon', 'reiselengde', 'avreise_dato', 'sist_varslet_pris')
    actions = ['kjør_varslingssjekk']

    def kjør_varslingssjekk(self, request, queryset):
        sjekk_abonnementer()
        self.message_user(request, "Varslingssjekk er kjørt.", level=messages.SUCCESS)
    kjør_varslingssjekk.short_description = "Kjør varslingssjekk nå"