from django.urls import path
from . import views  # Asegúrate que aquí importas tu views con @api_view

urlpatterns = [
    # ====================================================
    #   CASOS
    # ====================================================
    path('especializaciones/', views.get_especializaciones, name='get_especializaciones'),
    path('buscar_cliente/', views.buscar_cliente, name='buscar_cliente'),
    path('crear_caso/', views.crear_caso, name='crear_caso'),
    path('guardar_caso/', views.guardar_caso, name='guardar_caso'),

    # ====================================================
    #   EXPEDIENTES
    # ====================================================
    path('abogados/', views.get_abogados, name='get_abogados'),

    path('buscar_caso/<int:nocaso>/', views.buscar_caso, name='buscar_caso_expediente'),
    path('ciudades/', views.get_ciudades, name='get_ciudades'),
    path('crear_expediente/', views.crear_expediente, name='crear_expediente'),
    path('guardar_expediente/', views.guardar_expediente, name='guardar_expediente'),
]
