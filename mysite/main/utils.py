# main/utils.py
from .models import PrisAbonnement, VingData, VingURL
from django.core.mail import send_mail
from decouple import config



def hent_urls_for_scraping():
    return list(
        VingURL.objects.filter(aktiv=True).values_list('url', flat=True)
    )

def sjekk_abonnementer():
    for abo in PrisAbonnement.objects.all():
        treff = VingData.objects.filter(
            destinasjon__iexact=abo.destinasjon,
            reiselengde=abo.reiselengde,
            avreise_dato=abo.avreise_dato
        ).order_by('pris').first()

        if not treff:
            continue

        if abo.sist_varslet_pris is None:
            # Første gang: bare sett prisen, ikke send varsel
            abo.sist_varslet_pris = treff.pris
            abo.save()
            continue

        if treff.pris < abo.sist_varslet_pris:
            send_varsel(abo.bruker, treff)
            abo.sist_varslet_pris = treff.pris
            abo.save()


def send_varsel(bruker, vingdata):
    send_mail(
        subject=f"Prisfall: {vingdata.destinasjon}",
        message=(
            f"Ny pris: {vingdata.pris} kr for {vingdata.reiselengde} dager "
            f"fra {vingdata.avreisested} {vingdata.avreise_dato}.\n"
            f"Lenke: {vingdata.url}"
        ),
        from_email=str(config("EMAIL_HOST_USER")),
        recipient_list=[bruker.email],
    )