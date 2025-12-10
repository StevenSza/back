from django.contrib import admin
from django.urls import path, include
from casos.views_templates import caso_template

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Template/Interfaz HTML
    path('caso/', caso_template, name='cliente_template'),
    
    # API REST
    path('api/caso/', include('casos.api_urls')),
]