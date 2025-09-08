# Osteria di Citerna - il Galletto

## Descrizione
Il sito web del ristorante consente la visualizzazione della home page e del menù con immagini e filtri. Un utente anonimo può solo visualizzare le pagine precedentemente citate.
Un cliente Registrato può in più fare ordini e prenotare tavoli. La pagina del carrello gestisce le ordinazioni d'asporto. La pagina delle prenotazioni dei tavoli con gestione disponibilità e giorni non prenotabili. Dopo il login l'utente in fondo al menù potrà trovare 2 sistemi di raccomandazioni dei piatti: suggeriti per l'utente e i più poplari. C'è un'area amministrazione per gestire menù e prenotazioni degli utenti. L' admin ha accesso a tutte le funzionalità e la gestione del menù.



## Requisiti

- Python3
- Django
- SQLite
- Git


## Installazione

1. Clonare il repository da GitHub:
    git clone https://github.com/elegibellini/Progetto-Tecnologie-Web-2025.git
    cd osteria

2. Installare le dipendenze:
    pip3 install -r requirements.txt
    oppure 
    pipenv install

3. Applicare le migrazioni:
    python3 manage.py migrate

4. Avvviare il server:
    python3 manage.py runserver (8008)
    Il sito disponibile su http://127.0.0.1:8008
