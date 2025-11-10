from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from main.models import VingData

def parse_url_params(url: str) -> dict:
    parts = url.split("?", 1)
    if len(parts) < 2:
        return {}
    query = parts[1]
    params = {}
    for pair in query.split("&"):
        if "=" in pair:
            key, value = pair.split("=", 1)
            params[key] = value
    return params

class Command(BaseCommand):
    help = "Oppdaterer hjemreise_dato og reiselengde for eksisterende VingData basert på URL"

    def handle(self, *args, **kwargs):
        oppdatert = 0
        for rad in VingData.objects.all():
            params = parse_url_params(rad.url)
            avreise = rad.avreise_dato
            hjemreise = None
            lengde = None

            # QueryRetDate har høyest prioritet
            if "QueryRetDate" in params and params["QueryRetDate"]:
                try:
                    hjemreise = datetime.strptime(params["QueryRetDate"], "%Y%m%d").date()
                    if avreise:
                        lengde = (hjemreise - avreise).days
                except ValueError:
                    pass
            # Ellers bruk QueryDur
            elif "QueryDur" in params and params["QueryDur"]:
                try:
                    dur = int(params["QueryDur"])
                    # Ving "8 dager" = 7 netter → retur = avreise + (dur - 1)
                    if avreise and dur > 0:
                        hjemreise = avreise + timedelta(days=dur - 1)
                        lengde = dur - 1
                except ValueError:
                    pass

            if hjemreise and rad.hjemreise_dato != hjemreise:
                rad.hjemreise_dato = hjemreise
                if lengde is not None:
                    rad.reiselengde = lengde
                rad.save(update_fields=["hjemreise_dato", "reiselengde"])
                oppdatert += 1
                self.stdout.write(f"Oppdatert rad {rad.pk}: hjemreise={hjemreise}, lengde={lengde}")

        self.stdout.write(f"Totalt oppdatert {oppdatert} rader.")
