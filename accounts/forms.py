from django import forms
from .models import *
from datetime import date
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError


class AggiungiPiatto(ModelForm):
    class Meta:
        model = Piatto
        fields = '__all__'

class CreateUserForm(UserCreationForm):

    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Conferma Password', widget=forms.PasswordInput)
    email = forms.EmailField(label='Email personale')
    registrati_come_lavoratore = forms.BooleanField(required=False, label="Registrati come lavoratore")
    email_aziendale = forms.EmailField(required=False, label="Email aziendale (solo se lavoratore)")

    class Meta:
        model = User
        fields = ['username', 'email', 'registrati_come_lavoratore', 'email_aziendale', 'password1', 'password2']

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")

        if p1 and p2 and p1 != p2:
            raise ValidationError("Le password non coincidono.")
        
        is_worker = cleaned_data.get('registrati_come_lavoratore')
        email_aziendale = cleaned_data.get('email_aziendale')

        if is_worker and (not email_aziendale or not email_aziendale.endswith('@osteria.com')):
            raise ValidationError("Selezionato 'Lavoratore': fornire una mail @osteria.com valida.")


class PrenotazioneTavoloForm(forms.ModelForm):
    data = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'min': date.today().isoformat()}),
        label="Data della prenotazione"
    )

    scelta=[
        ("19:30", "19:30"),
        ("20:00", "20:00"),
        ("20:30", "20:30"),
        ("21:00", "21:00"),
    ]
    

    ora = forms.ChoiceField(
        choices=scelta,
        label="Ora della prenotazione",
        widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = Prenotazione
        fields = ['data', 'ora', 'numero_persone']
        labels = {
            'numero_persone': 'Numero di persone'
        }


class GiornoNonPrenotabileForm(forms.ModelForm):
    data = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date','min': date.today().isoformat()}),
        label="Data da bloccare"
    )

    class Meta:
        model = GiornoNonPrenotabile
        fields = ['data']
