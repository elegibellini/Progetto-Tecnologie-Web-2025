from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home_custom, name='home'),
    path('registrati/', views.registrati, name='registrati'),
    path('logout/', views.logout_view, name='logout'),
    path('login/', views.paginaLogin, name='login'),
    path('amministrazione/', views.amministrazione, name='amministrazione'),
    path('non_autorizzato/', views.non_autorizzato, name='non_autorizzato'),
    path('prenota/', views.prenota_tavolo, name='prenota_tavolo'),
    path('riepilogo-prenotazione/', views.riepilogo_prenotazione, name='riepilogo_prenotazione'),
    path('cerca_piatto/', views.cerca_piatto, name='cerca_piatto'),
    path('aggiungi_al_carrello/<int:piatto_id>/', views.aggiungi_al_carrello, name='aggiungi_al_carrello'),
    path('carrello/', views.visualizza_ordinazione, name='visualizza_ordinazione'),
    path('invia_ordinazione/', views.invia_ordinazione,name='invia_ordinazione'),
    path('rimuovi_piatto/<int:ordinazione_id>/', views.rimuovi_piatto, name='rimuovi_piatto'),
    path('carrello/aggiungi/<int:ordinazione_id>/', views.aggiungi_quantita, name='aggiungi_quantita'),
    path('diminuisci/<int:ordinazione_id>/', views.diminuisci_quantita, name='diminuisci_quantita'),
    path('area-lavoratori/', views.area_lavoratori, name='area_lavoratori'),
    path('gestione-prenotazioni/', views.gestione_prenotazioni, name='gestione_prenotazioni'),
    path('area_personale/', views.area_personale, name='area_personale'),
    path('storico_ordini/', views.storico_ordini, name='storico_ordini'),
    path('menu/', views.menu, name='menu'),
    path('storico-ordini/', views.storico_ordini_completo, name='storico_ordini_completo'),
    path('elimina-prenotazione/<int:prenotazione_id>/', views.elimina_prenotazione, name='elimina_prenotazione'),
    path('modifica-prenotazione/<int:prenotazione_id>/', views.modifica_prenotazione, name='modifica_prenotazione'),



    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
