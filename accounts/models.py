from django.db import models
from django.contrib.auth.models import User



class Utente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nome = models.CharField(max_length=25, null=True)
    cognome = models.CharField(max_length=25, null=True)
    email = models.CharField(max_length=30, null=True)
    data_creazione = models.DateTimeField(auto_now_add=True)
    saldo_punti = models.IntegerField(default=0)

    
    def __str__(self):
        return self.nome

    class Meta:
        verbose_name_plural = 'Utenti'


class Portata(models.Model):
    nome = models.CharField(max_length=50)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name_plural = 'Portate'

class Piatto(models.Model):
    nome = models.CharField(max_length=50)
    ingredienti = models.CharField(max_length=500, null=True, blank=True)
    prezzo = models.FloatField(null=True)
    portata = models.ManyToManyField(Portata)
    immagine = models.ImageField(upload_to='piatti/', null=True, blank=True)


    
    def __str__(self):
        return self.nome

    class Meta:
        verbose_name_plural = 'Piatti'

class Tavolo(models.Model):
    tipologie=[
        ('piccolo', 'Piccolo (1,3 persone)'),
        ('grande', 'Grande (3-6 persone)')
    ]

    tipo = models.CharField(max_length=10, choices=tipologie)
    numero = models.PositiveIntegerField(unique=True) 
    capienza_massima = models.PositiveIntegerField()

    def __str__(self):
        return f"Tavolo {self.numero} ({self.tipo} - {self.capienza_massima} posti)"

class Prenotazione(models.Model):
    utente = models.ForeignKey(User, on_delete=models.CASCADE)
    data = models.DateField()
    ora = models.TimeField()
    numero_persone = models.PositiveIntegerField()
    creato_il = models.DateTimeField(auto_now_add=True)
    tavoli_assegnati = models.ManyToManyField(Tavolo, blank=True)

    def __str__(self):
        return f"{self.utente.username} - {self.data} {self.ora} - {self.numero_persone} persone"



class Ordinazione(models.Model):
    utente = models.ForeignKey(User, on_delete=models.CASCADE, null=True, default=1)
    piatto = models.ForeignKey(Piatto, on_delete=models.CASCADE, default=None) 
    quantita = models.PositiveIntegerField(default=1)
    completato = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Ordinazioni'


class GiornoNonPrenotabile(models.Model):
    data = models.DateField(unique=True)

    def __str__(self):
        return self.data.strftime("%d/%m/%Y")
    
