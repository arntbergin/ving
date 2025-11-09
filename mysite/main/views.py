from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models.functions import Lower
from .utils import sjekk_abonnementer
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import VingData, PrisAbonnement, VingURL, PersonligURL
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
def ving_aktiv(request):
    kategori = request.GET.get('k')
    valgt_id = request.GET.get('s')

    # Nullstill kategori hvis spesifikt søk er valgt
    if valgt_id:
        kategori = None

    # Lag identifikator med prefiks
    felles_sok = [(f"ving_{sok.pk}", sok, False) for sok in VingURL.objects.filter(aktiv=True).order_by(Lower('navn'))]
    personlige_sok = [(f"personlig_{sok.pk}", sok, True) for sok in PersonligURL.objects.filter(bruker=request.user).order_by(Lower('navn'))]
    aktive_sok = felles_sok + personlige_sok

    siste_dato = VingData.objects.order_by('-dato_skrapt').values_list('dato_skrapt', flat=True).first()
    if not siste_dato:
        messages.warning(request, "Ingen reiser funnet.")
        return redirect('ving_liste')

    data = VingData.objects.filter(dato_skrapt=siste_dato)

# Filtrering
    if valgt_id:
        for sok_id, sok_obj, _ in aktive_sok:
            if sok_id == valgt_id:
                data = data.filter(url=sok_obj.url)
                break
    elif kategori == 'felles':
        urls = [sok.url for _, sok, _ in felles_sok]
        data = data.filter(url__in=urls)
    elif kategori == 'personlig':
        urls = [sok.url for _, sok, _ in personlige_sok]
        data = data.filter(url__in=urls)
    else:  # Alle = felles + egne personlige
        urls = [sok.url for _, sok, _ in felles_sok + personlige_sok]
        data = data.filter(url__in=urls)

    data = data.order_by('pris')

    abonnementer = PrisAbonnement.objects.filter(bruker=request.user)
    aktive_nokler = set(
        (a.destinasjon.strip().lower(), int(a.reiselengde), a.avreise_dato)
        for a in abonnementer
    )

    data_liste = []
    for rad in data:
        nokkel = (rad.destinasjon.strip().lower(), int(rad.reiselengde), rad.avreise_dato)
        data_liste.append({
            "obj": rad,
            "har_abonnement": nokkel in aktive_nokler
        })

    kolonner = [
        ('avreisested', 'Avreisested'),
        ('destinasjon', 'Destinasjon'),
        ('pris', 'Pris'),
        ('avreise_dato', 'Avreise'),
        ('reiselengde', 'Lengde'),
        ('dato_skrapt', 'Dato sjekket'),
    ]

    return render(request, 'ving_liste.html', {
        'data': data_liste,
        'current_sort': None,
        'columns': kolonner,
        'title': 'Ving',
        'aktive_sok': aktive_sok,
        'valgt_id': valgt_id,
        'kategori': kategori,
    })


@login_required
def ving_historikk(request):
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

    return render(request, 'ving_historikk.html', {
        'title': 'Ving - Prishistorikk',
        'data': data,
        'current_sort': sort,
        'columns': columns,
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

@login_required
def personlig_sok(request):
    if request.method == 'POST':
        navn = request.POST.get('navn')
        url = request.POST.get('url')
        if navn and url:
            PersonligURL.objects.create(bruker=request.user, navn=navn, url=url)
            return redirect('personlig_sok')

    mine_urler = PersonligURL.objects.filter(bruker=request.user)
    context = {
        'mine_urler': mine_urler,
    }
    return render(request, 'personlig_sok.html', context)


@login_required
def slett_personlig_url(request, url_id):
    url = get_object_or_404(PersonligURL, id=url_id, bruker=request.user)
    url.delete()
    return HttpResponseRedirect(reverse('personlig_sok'))