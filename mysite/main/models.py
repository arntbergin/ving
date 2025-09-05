from django.db import models
from django.conf import settings

class VingURL(models.Model):
    navn = models.CharField(max_length=500, help_text="Beskrivende navn, f.eks. 'Mallorca 8 dager'")
    url = models.URLField()
    aktiv = models.BooleanField(default=True, help_text="Brukes i scraping hvis aktivert")

    opprettet = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.navn

class VingData(models.Model):
    avreisested = models.CharField(max_length=500)
    destinasjon = models.CharField(max_length=500)
    pris = models.IntegerField()
    url = models.URLField(max_length=500)
    avreise_dato = models.DateField()  # midlertidig tillat null
    reiselengde = models.IntegerField()
    dato_skrapt = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.destinasjon} fra {self.avreisested} - {self.pris} NOK"
    
class PrisAbonnement(models.Model):
    bruker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    destinasjon = models.CharField(max_length=500)
    reiselengde = models.IntegerField()
    avreise_dato = models.DateField()
    sist_varslet_pris = models.IntegerField(null=True, blank=True)
    opprettet = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bruker} → {self.destinasjon} ({self.reiselengde} dager fra {self.avreise_dato})"
    

