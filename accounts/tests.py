from django.test import TestCase
from django.contrib.auth.models import User, Group
from accounts.models import Utente
from django.contrib.auth.hashers import make_password
from .models import Piatto, Ordinazione, Prenotazione, GiornoNonPrenotabile
from datetime import date, timedelta, time
from time import sleep
from django.urls import reverse

#verifica se il modello utente funziona
class UtenteModelTest(TestCase):
    def create_test_user(self, username="testuser", password="123456", email=''):
        return User.objects.create(username=username, password=make_password(password), email=email)

    def test_creazione_utente(self):
        test_user = self.create_test_user()

        # Attendi 1 secondo per consentire la sincronizzazione dei dati del database
        sleep(1)
        
        self.assertIsInstance(test_user, User)
        self.assertEqual(test_user.username, "testuser")
        
        utente_associato, created = Utente.objects.get_or_create(user=test_user)
        self.assertIsInstance(utente_associato, Utente)
        self.assertEqual(utente_associato.saldo_punti, 0)


#area personale mostra i giusti dati
class AreaPersonaleTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='cliente', password='test123', email='cliente@test.com')
        Utente.objects.create(user=self.user, saldo_punti=150)

    def test_visualizzazione_area_personale(self):
        self.client.login(username='cliente', password='test123')
        response = self.client.get(reverse('area_personale'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Area Personale")
        self.assertContains(response, "cliente@test.com")
        self.assertContains(response, "150")

#test sul carrello e sulla conferma
class OrdinazioneViewTest(TestCase):
    def setUp(self):
        self.utente_normale = User.objects.create_user(username='utente_normale', password='password123')
        self.pasta = Piatto.objects.create(nome='Pasta', prezzo=10.00)

    def test_aggiungi_al_carrello_view(self):
        
        self.client.login(username='utente_normale', password='password123')
        response = self.client.post(reverse('aggiungi_al_carrello', args=[self.pasta.id]), follow=True)
        self.assertEqual(response.status_code, 200)

        ordinazione = Ordinazione.objects.filter(utente=self.utente_normale, piatto=self.pasta, completato=False).first()
        self.assertIsNotNone(ordinazione)
        self.assertEqual(ordinazione.quantita, 1)

    def test_invia_ordinazione_view(self):

        self.client.login(username='utente_normale', password='password123')
        response = self.client.post(reverse('invia_ordinazione'))
        self.assertEqual(response.status_code, 302)

        sleep(1)

        ordinazione = Ordinazione.objects.filter(utente=self.utente_normale, completato=True).first()
        self.assertRedirects(response, reverse('home'))

#prenotazioni future e che funzionino i "blocchi"
class PrenotazioneViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='cliente', password='test123')
        self.client.login(username='cliente', password='test123')

    def test_prenotazione_valida(self):
        data_futura = date.today() + timedelta(days=3)
        response = self.client.post(reverse('prenota_tavolo'), {
            'data': data_futura,
            'ora': '20:00',
            'numero_persone': 2,
        })
        self.assertRedirects(response, reverse('riepilogo_prenotazione'))

    def test_prenotazione_data_passata(self):
            data_passata = date.today() - timedelta(days=1)
            response = self.client.post(reverse('prenota_tavolo'), {
                'data': data_passata,
                'ora': '20:00',
                'numero_persone': 2,
            })
            self.assertRedirects(response, reverse('prenota_tavolo'))

    def test_prenotazione_lunedi(self):
        oggi = date.today()
        giorni_avanti = (0 - oggi.weekday()) % 7
        prossimo_lunedi = oggi + timedelta(days=giorni_avanti or 7)

        response = self.client.post(reverse('prenota_tavolo'), {
            'data': prossimo_lunedi,
            'ora': '20:00',
            'numero_persone': 2,
        })
        self.assertRedirects(response, reverse('prenota_tavolo'))

    def test_prenotazione_giorno_bloccato(self):
        data_bloccata = date.today() + timedelta(days=2)
        GiornoNonPrenotabile.objects.create(data=data_bloccata)

        response = self.client.post(reverse('prenota_tavolo'), {
            'data': data_bloccata,
            'ora': '20:00',
            'numero_persone': 2,
        })
        self.assertRedirects(response, reverse('prenota_tavolo'))