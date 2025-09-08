
from django.contrib import admin
from django.urls import include, path

import accounts
from accounts import urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(accounts.urls))

]
