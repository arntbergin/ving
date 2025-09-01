
from django import forms
from .models import PrisAbonnement

class PrisAbonnementForm(forms.ModelForm):
    class Meta:
        model = PrisAbonnement
        fields = ['destinasjon', 'reiselengde', 'avreise_dato']