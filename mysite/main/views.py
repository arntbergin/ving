from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models.functions import Lower
from .utils import sjekk_abonnementer
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import VingData, PrisAbonnement, VingURL
from .forms import PrisAbonnementForm


@staff_member_required
def trigge_sjekk_abonnementer(request):
    sjekk_abonnementer()
    messages.success(request, "Varslingssjekk er kjørt.")
    return redirect('admin') 

@login_required
def home(request: HttpRequest) -> HttpResponse:
    return render(request, 'main/home.html')

@login_required
def ving_nåbilde(request):
    # Hent alle aktive søk til topp-listen
    aktive_søk = VingURL.objects.filter(aktiv=True).order_by(Lower('navn'))

    # Hent valgt søk fra query-param (?s=<id>)
    valgt_id = request.GET.get('s')

    # Finn siste scraping-dato
    siste_dato = VingData.objects.order_by('-dato_skrapt').values_list('dato_skrapt', flat=True).first()
    if not siste_dato:
        messages.warning(request, "Ingen reiser funnet.")
        return redirect('ving_liste')

    # Start med alle rader fra siste scraping
    data = VingData.objects.filter(dato_skrapt=siste_dato)

    # Hvis et søk er valgt, filtrer på det
    if valgt_id:
        valgt_url = aktive_søk.filter(pk=valgt_id).values_list('url', flat=True).first()
        if valgt_url:
            data = data.filter(url=valgt_url)

    # Sorter etter pris
    data = data.order_by('pris')

    columns = [
        ('avreisested', 'Avreisested'),
        ('destinasjon', 'Destinasjon'),
        ('pris', 'Pris'),
        ('avreise_dato', 'Avreise'),
        ('reiselengde', 'Lengde'),
        ('dato_skrapt', 'Dato sjekket'),
    ]

    return render(request, 'ving_liste.html', {
        'data': data,
        'current_sort': None,
        'columns': columns,
        'title': 'Ving',
        'aktive_søk': aktive_søk,
        'valgt_id': str(valgt_id) if valgt_id else '',
    })


@login_required
def ving_liste(request):
    # Definer kolonner som (felt, visningsnavn)
    columns = [
        ('avreisested', 'Avreisested'),
        ('destinasjon', 'Destinasjon'),
        ('pris', 'Pris'),
        ('avreise_dato', 'Avreise'),
        ('reiselengde', 'Lengde'),
        ('dato_skrapt', 'Dato sjekket'),
    ]

    # Hent ønsket sortering fra URL, standard: nyeste først
    sort = request.GET.get("sort", "-dato_skrapt")

    # Tillatte felter for sortering
    allowed_sorts = [col[0] for col in columns]

    # Sjekk at feltet er gyldig
    if sort.lstrip('-') not in allowed_sorts:
        sort = "-dato_skrapt"

    data = VingData.objects.all().order_by(sort)

    return render(request, 'ving_liste.html', {
        'data': data,
        'current_sort': sort,
        'columns': columns,
        'title': 'Ving - Prishistorikk'
    })




@login_required
def nytt_abonnement(request):
    if request.method == 'POST':
        print("POST-data mottatt:", request.POST)  # Debug i terminalen

        form = PrisAbonnementForm(request.POST)
        if form.is_valid():
            abo = form.save(commit=False)
            abo.bruker = request.user
            abo.save()
            print("✅ Abonnement lagret:", abo)
            return redirect('mine_abonnement')
        else:
            print("❌ Skjemaet er ugyldig:", form.errors)  # Debug i terminalen
    else:
        form = PrisAbonnementForm()

    return render(request, 'nytt_abonnement.html', {'form': form})

@login_required
def mine_abonnement(request):
    abonnementer = PrisAbonnement.objects.filter(bruker=request.user)
    return render(request, 'mine_abonnement.html', {'abonnementer': abonnementer})

@login_required
def slett_abonnement(request, abo_id):
    abo = get_object_or_404(PrisAbonnement, id=abo_id, bruker=request.user)
    abo.delete()
    return redirect('mine_abonnement')
