from django.http import HttpResponse
from django.shortcuts import redirect


# Se l'utente ha già fatto l'accesso, non gli lasciamo vedere la pagina di login
def utente_non_autenticato(viewfunc):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        else:
            return viewfunc(request, *args, **kwargs)
    return wrapper_func


# Restringe la "visibilità" di una pagina solo ad alcuni gruppi di utenti
def utenti_autorizzati(ruoli_autorizzati=[]):
    def decorator(viewfunc):
        def wrapper_func(request, *args, **kwargs):

            group = None
            if request.user.groups.exists():
                group = request.user.groups.all()[0].name

            if group in ruoli_autorizzati:
                return viewfunc(request, *args, **kwargs)
            else:
                return redirect('non_autorizzato')
        return wrapper_func
    return decorator
