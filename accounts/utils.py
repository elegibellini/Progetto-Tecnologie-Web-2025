from .models import Tavolo, Prenotazione
from django.db.models import Q

def trova_tavoli_per_prenotazione(data, ora, numero_persone):
    
    tavoli_occupati = Prenotazione.objects.filter(
        data=data,
        ora=ora
    ).values_list('tavoli_assegnati__id', flat=True)

    
    tavoli_disponibili = Tavolo.objects.exclude(id__in=tavoli_occupati)

    #max 3 tavoli
    from itertools import combinations

    combinazioni_possibili = []
    for r in range(1, 4):  #da 1 a 3 tavoli
        for combo in combinations(tavoli_disponibili, r):
            somma = sum([t.capienza_massima for t in combo])
            penalita = (r - 1) * 2  # 2 posti persi per ogni unione per capotavola
            capienza_effettiva = somma - penalita
            if capienza_effettiva >= numero_persone:
                combinazioni_possibili.append((combo, capienza_effettiva))

    if not combinazioni_possibili:
        return None  

    
    combinazioni_possibili.sort(key=lambda x: (len(x[0]), x[1] - numero_persone))
    tavoli_assegnati = combinazioni_possibili[0][0]
    return tavoli_assegnati
