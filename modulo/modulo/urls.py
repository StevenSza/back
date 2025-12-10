from django.urls import path
from .views_templates import cliente_template

urlpatterns = [
    path('caso/', cliente_template, name='cliente_template'),
]
