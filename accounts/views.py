from django.shortcuts import get_object_or_404, render, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from .decorators import *
import json
from .utils import trova_tavoli_per_prenotazione
from accounts.forms import CreateUserForm
from django.views.generic.edit import CreateView
from .models import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import Group
from .forms import AggiungiPiatto
from django.db.models import Q, Count
from .forms import PrenotazioneTavoloForm, GiornoNonPrenotabileForm
from datetime import datetime, date, timedelta


def dashboard(request):
    piatti = Piatto.objects.all()
    portate = Portata.objects.all()
    return render(request, 'dashboard.html', {
        'piatti': piatti,
        'portate': portate
    })

def home_custom(request):
    return render(request, 'accounts/home.html')


@utente_non_autenticato
def registrati(request):
    form= CreateUserForm()
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()

            Utente.objects.create(user=user, nome=user.username)

            if form.cleaned_data.get('registrati_come_lavoratore'):
                gruppo_lavoratori, _ = Group.objects.get_or_create(name='Lavoratori')
                user.groups.add(gruppo_lavoratori)

            messages.success(request, f'{user.username}, registrazione avvenuta con successo!')
            return redirect('login')

    return render(request, 'accounts/registrati.html', {'form': form})


@utente_non_autenticato
def paginaLogin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.info(request, 'Per favore ricontrolla Username o Password.')

    return render(request, 'accounts/login.html')


def genera_raccomandazioni(utente):
    portate_preferite = Ordinazione.objects.filter(utente=utente, completato=True).values_list('piatto__portata__nome', flat=True)

    frequenza_portate = {}
    for portata in portate_preferite:
        frequenza_portate[portata] = frequenza_portate.get(portata, 0) + 1

    portate_ordinate = sorted(frequenza_portate.items(), key=lambda x: x[1], reverse=True)

    portata_piu_amata = None
    if portate_ordinate:
        portata_piu_amata = portate_ordinate[0][0]

    raccomandazioni = Piatto.objects.filter(portata__nome=portata_piu_amata)

    return raccomandazioni, portata_piu_amata


def menu(request):
    ordine = request.GET.get('ordine', 'prezzo_asc')
    portata = request.GET.get('portata', 'Tutti')
    portata = portata.capitalize()

    piatti = Piatto.objects.all()
    portate = Portata.objects.all()

    if portata != 'Tutti':
        piatti = piatti.filter(portata__nome=portata)

    if ordine == 'prezzo_asc':
        piatti = piatti.order_by('prezzo')
    elif ordine == 'nome':
        piatti = piatti.order_by('nome')

    
    suggeriti = []
    preferiti = []

    if request.user.is_authenticated:
        #piatti utente
        piatti_utente = (Ordinazione.objects
            .filter(utente=request.user, completato=True)
            .values("piatto")
            .annotate(count=Count("piatto"))
            .order_by("-count")[:4])
        suggeriti = Piatto.objects.filter(id__in=[p["piatto"] for p in piatti_utente])

    #piatti totali
    piatti_popolari = (Ordinazione.objects
        .filter(completato=True)
        .values("piatto")
        .annotate(count=Count("piatto"))
        .order_by("-count")[:4])
    preferiti = Piatto.objects.filter(id__in=[p["piatto"] for p in piatti_popolari])

    
    piatti_per_portata = {}
    for cat in portate:
        piatti_cat = piatti.filter(portata=cat)
        if piatti_cat.exists():
            piatti_per_portata[cat.nome] = piatti_cat

    return render(request, 'accounts/dashboard.html', {
        'piatti': piatti,
        'portate': portate,
        'categoria': portata,
        'ordine': ordine,
        'piatti_per_categoria': piatti_per_portata,
        'suggeriti': suggeriti,
        'preferiti': preferiti,
    })


def logout_view(request):
    logout(request)
    return redirect('home')


def is_manager(user):
    return user.groups.filter(name='Manager').exists()


def non_autorizzato(request):
    return render(request, 'accounts/non_autorizzato.html')


@login_required
def amministrazione(request):
    if not (request.user.groups.filter(name__in=['Manager', 'Lavoratori']).exists() or request.user.is_superuser):
        return redirect('non_autorizzato')
    if request.method == 'POST' and 'blocca_giorno' in request.POST:
        form_giorno = GiornoNonPrenotabileForm(request.POST)
        if form_giorno.is_valid():
            form_giorno.save()
            messages.success(request, "Giorno bloccato con successo!")
            return redirect('amministrazione')
    else:
        form_giorno = GiornoNonPrenotabileForm()

    oggi=date.today()
    prenotazioni_future = Prenotazione.objects.filter(
        data__gte=oggi
    ).order_by('data', 'ora')
    
    giorni_bloccati = GiornoNonPrenotabile.objects.filter(data__gte=oggi).values_list('data', flat=True)
    giorni_bloccati_js = json.dumps([g.strftime('%Y-%m-%d') for g in giorni_bloccati])

    return render(request, 'accounts/amministrazione.html', {
        'prenotazioni_future': prenotazioni_future,
        'giorni_bloccati': giorni_bloccati,
        'form_giorno': form_giorno,
        'giorni_bloccati_js': giorni_bloccati_js
    })


def cerca_piatto(request):
    query = request.GET.get('q')
    piatti = Piatto.objects.filter(Q(nome__icontains=query) | Q(ingredienti__icontains=query))
    return render(request, 'accounts/cerca_piatto.html', {'piatti': piatti, 'query': query})


@login_required
def prenota_tavolo(request):
    oggi=date.today()
    giorni_no = GiornoNonPrenotabile.objects.filter(data__gte=oggi).values_list('data', flat=True)

    if request.method == 'POST':
        form = PrenotazioneTavoloForm(request.POST)
        if form.is_valid():
            prenotazione = form.save(commit=False)
            prenotazione.utente = request.user

            if prenotazione.data < oggi:
                messages.error(request, "Non puoi prenotare per una data passata.")
                return redirect('prenota_tavolo')

            elif prenotazione.data in giorni_no:
                messages.error(request, "Ci scusiamo, ma la data selezionata non è disponibile per le prenotazioni.")
                return redirect('prenota_tavolo')

            elif prenotazione.data.weekday() == 0:
                messages.error(request, "Ci dispiace, siamo chiusi il lunedì.")
                return redirect('prenota_tavolo')
            else:
                request.session['prenotazione_temp'] = {
                    'data': str(prenotazione.data),
                    'ora': str(prenotazione.ora),
                    'numero_persone': prenotazione.numero_persone
                }
                return redirect('riepilogo_prenotazione')
    else:
        form = PrenotazioneTavoloForm()

    return render(request, 'accounts/prenota_tavolo.html', {
        'form': form,
        'giorni_bloccati': giorni_no
    })


@login_required
def riepilogo_prenotazione(request):
    if request.method == 'POST':

        data = request.POST.get('data')
        ora = request.POST.get('ora')
        numero_persone = int(request.POST.get('numero_persone'))
        data=datetime.strptime(data, '%Y-%m-%d').date()
        ora = datetime.strptime(ora, '%H:%M:%S').time()

        tavoli = trova_tavoli_per_prenotazione(data, ora, numero_persone)

        if tavoli is None:
            return render(request, 'accounts/prenotazione_fallita.html')

        prenotazione = Prenotazione.objects.create(
            data=data,
            ora=ora,
            numero_persone=numero_persone,
            utente=request.user
        )
        prenotazione.tavoli_assegnati.set(tavoli)
        prenotazione.save()

        if 'prenotazione_temp' in request.session:
            del request.session['prenotazione_temp']

        return render(request, 'accounts/prenotazione_riuscita.html', {
            'data': data,
            'ora': ora
        })

    dati = request.session.get('prenotazione_temp')
    if not dati:
        return redirect('prenota_tavolo')

    prenotazione2 = {
        'data': dati['data'],
        'ora': dati['ora'],
        'numero_persone': dati['numero_persone'],
        'nome_utente': request.user.username
    }

    return render(request, 'accounts/riepilogo_prenotazione.html', {
        'prenotazione': prenotazione2
    })


def aggiungi_al_carrello(request, piatto_id):
    if request.method == 'POST':
        piatto = get_object_or_404(Piatto, id=piatto_id)
        utente = request.user
        ordinazioni = Ordinazione.objects.filter(utente=utente, piatto=piatto, completato=False)

        if ordinazioni.exists():
            ordinazione = ordinazioni.first()
            ordinazione.quantita += 1
            ordinazione.save()
        else:
            Ordinazione.objects.create(utente=utente, piatto=piatto, quantita=1)

        return redirect('menu')
    else:
        return JsonResponse({'status': 'error'})

def is_lavoratore(user):
    return user.groups.filter(name='Lavoratori').exists()

@user_passes_test(is_lavoratore)
def area_lavoratori(request):
    oggi = date.today()

    if request.method == 'POST':
        form = GiornoNonPrenotabileForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('area_lavoratori')
    else:
        form = GiornoNonPrenotabileForm()

    prenotazioni_future = Prenotazione.objects.filter(data__gte=oggi).order_by('data', 'ora')
    prenotazioni_passate = Prenotazione.objects.filter(data__lt=oggi).order_by('-data', '-ora')
    giorni_bloccati = GiornoNonPrenotabile.objects.filter(data__gte=oggi).order_by('data')

    return render(request, 'accounts/area_lavoratori.html', {
        'prenotazioni_future': prenotazioni_future,
        'prenotazioni_passate': prenotazioni_passate,
        'giorni_bloccati': giorni_bloccati,
        'form': form
    })

@user_passes_test(is_lavoratore)
def gestione_prenotazioni(request):
    oggi = date.today()
    future = Prenotazione.objects.filter(data__gte=oggi).order_by('data', 'ora')
    passate = Prenotazione.objects.filter(data__lt=oggi).order_by('-data', '-ora')

    return render(request, 'accounts/gestione_prenotazioni.html', {
        'prenotazioni_future': future,
        'prenotazioni_passate': passate
    })

def calcola_dati_ordinazione(ordinazioni, utente):
    totale = sum(ordinazione.piatto.prezzo * ordinazione.quantita for ordinazione in ordinazioni)
    punti = 0

    punti = (int(totale) // 50) * 100

    return {
        'totale_ordine': totale,
        'punti': punti,
    }


def visualizza_ordinazione(request):
    if request.user.is_authenticated:
        ordinazioni = Ordinazione.objects.filter(utente=request.user, completato=False)
        dati_ordinazione = calcola_dati_ordinazione(ordinazioni, request.user)
        dati_ordinazione['ordinazioni'] = ordinazioni
        return render(request, 'accounts/carrello.html', dati_ordinazione)

    return render(request, 'home')

@login_required
def invia_ordinazione(request):
    utente = request.user
    ordini = Ordinazione.objects.filter(utente=utente, completato=False)

    if ordini.exists():
        dati = calcola_dati_ordinazione(ordini, utente)
        totale = dati['totale_ordine']
        punti = dati['punti']
        utente.utente.saldo_punti += punti
        utente.utente.save()
        

        ordini.update(completato=True)
        messages.success(request, f"Ordine confermato! Ti aspettiamo in osteria per il ritiro. Hai ottenuto {punti} punti!")
        return redirect('home') 
   
    return redirect('home')

@login_required
def aggiungi_quantita(request, ordinazione_id):
    ordinazione = get_object_or_404(Ordinazione, id=ordinazione_id, utente=request.user, completato=False)
    ordinazione.quantita += 1
    ordinazione.save()
    return redirect('visualizza_ordinazione')

@login_required
def diminuisci_quantita(request, ordinazione_id):
    ordinazione = get_object_or_404(
        Ordinazione, id=ordinazione_id, utente=request.user, completato=False
    )
    if ordinazione.quantita > 1:
        ordinazione.quantita -= 1
        ordinazione.save()
    else:
        ordinazione.delete()
    return redirect('visualizza_ordinazione')

@login_required
def rimuovi_piatto(request, ordinazione_id):
    ordinazione = get_object_or_404(
        Ordinazione, id=ordinazione_id, utente=request.user, completato=False
    )
    ordinazione.delete()  #elimina sempre il piatto
    return redirect('visualizza_ordinazione')

@login_required
def area_personale(request):
    oggi= date.today()
    utente= request.user
    utente_profile, _ = Utente.objects.get_or_create(user=utente)
    email=utente.email
    punti= utente.utente.saldo_punti
    prenotazioni_attive = Prenotazione.objects.filter(
        utente=request.user,
        data__gte=oggi
    ).order_by('data', 'ora')

    prenotazioni_passate = Prenotazione.objects.filter(
        utente=request.user,
        data__lt=oggi
    ).order_by('-data', '-ora')

    prenotazioni_attive_mod = []
    for p in prenotazioni_attive:
        modificabile = (p.data - oggi) >= timedelta(days=4)
        prenotazioni_attive_mod.append({
            'obj': p,
            'modificabile': modificabile,
        })

    return render(request, 'accounts/area_personale.html', {
        'username': utente.username,
        'email': email,
        'punti': punti,
        'prenotazioni_attive_mod': prenotazioni_attive_mod,
        'prenotazioni_attive': prenotazioni_attive,
        'prenotazioni_passate': prenotazioni_passate,
    })

@login_required
def storico_ordini(request):
    ordinazioni = Ordinazione.objects.filter(
        utente=request.user,
        completato=True
    ).order_by('-id')

    from datetime import date
    prenotazioni = Prenotazione.objects.filter(
        utente=request.user,
        data__lt=date.today()
    ).order_by('-data', '-ora')

    return render(request, 'accounts/storico_ordini.html', {
         'ordinazioni': ordinazioni,
         'prenotazioni': prenotazioni,
     })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def storico_ordini_completo(request):
    ordinazioni = Ordinazione.objects.filter(completato=True).order_by('-id')
    prenotazioni = Prenotazione.objects.filter(data__lt=date.today()).order_by('-data', '-ora')

    return render(request, 'accounts/storico_ordini_completo.html', {
        'ordinazioni': ordinazioni,
        'prenotazioni': prenotazioni,
    })


@login_required
def elimina_prenotazione(request, prenotazione_id):
    prenotazione = get_object_or_404(Prenotazione, id=prenotazione_id, utente=request.user)
    if prenotazione.data - date.today() >= timedelta(days=4):
        prenotazione.delete()
        messages.success(request, "Prenotazione eliminata con successo.")
    else:
        messages.error(request, "Non puoi eliminare una prenotazione meno di 4 giorni prima.")
    return redirect('area_personale')


@login_required
def modifica_prenotazione(request, prenotazione_id):
    prenotazione = get_object_or_404(Prenotazione, id=prenotazione_id, utente=request.user)
    if prenotazione.data - date.today() < timedelta(days=4):
        messages.error(request, "Non puoi modificare una prenotazione meno di 4 giorni prima.")
        return redirect('area_personale')
    if request.method == 'POST':
        form = PrenotazioneTavoloForm(request.POST)
        if form.is_valid():
            data_nuova = form.cleaned_data['data']
            ora_nuova = form.cleaned_data['ora']
            numero_persone_nuovo = form.cleaned_data['numero_persone']
            from .utils import trova_tavoli_per_prenotazione
            tavoli = trova_tavoli_per_prenotazione(data_nuova, ora_nuova, numero_persone_nuovo)
            if tavoli is None:
                messages.error(request, "Non ci sono tavoli disponibili per la nuova prenotazione.")
                return render(request, 'accounts/prenota_tavolo.html', {'form': form})
            prenotazione.delete()  
            nuova_prenotazione = Prenotazione.objects.create(
                utente=request.user,
                data=data_nuova,
                ora=ora_nuova,
                numero_persone=numero_persone_nuovo
            )
            nuova_prenotazione.tavoli_assegnati.set(tavoli)
            nuova_prenotazione.save()
            messages.success(request, "Prenotazione modificata con successo.")
            return redirect('area_personale')
    else:
        initial = {
            'data': prenotazione.data,
            'ora': prenotazione.ora,
            'numero_persone': prenotazione.numero_persone
        }
        form = PrenotazioneTavoloForm(initial=initial)
    return render(request, 'accounts/prenota_tavolo.html', {'form': form, 'modifica': True})
