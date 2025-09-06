from django.core.management.base import BaseCommand
from main.utils import sjekk_abonnementer

class Command(BaseCommand):
    help = "Sjekker prisabonnementer og sender varsler"

    def handle(self, *args, **kwargs):
        sjekk_abonnementer()
