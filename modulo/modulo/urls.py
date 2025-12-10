from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/caso/', include('casos.api_urls')),
    path('api/', include('casos.api_urls')),  # Para las rutas generales como abogados, ciudades
]